import hashlib
import json
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artifact, Experiment, Job, JobMetric
from app.schemas import ArtifactOut, ExperimentCreate, ExperimentOut
from app.routers.metrics import record_job_submitted
from worker.runner import submit_job

router = APIRouter(prefix="/experiments", tags=["experiments"])

# In-memory map of job_id → Ray ObjectRef (or Future)
# In production this would be persisted to Redis / Ray Jobs API
_futures: Dict[str, Any] = {}


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def _env_hash() -> str:
    try:
        import importlib.metadata
        pkgs = sorted(
            f"{d.name}=={d.version}"
            for d in importlib.metadata.distributions()
        )
        return hashlib.sha256("\n".join(pkgs).encode()).hexdigest()[:16]
    except Exception:
        return "unknown"


def _dataset_version(dataset_id: str) -> str:
    return hashlib.sha256(dataset_id.encode()).hexdigest()[:16]


@router.get("/", response_model=List[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return (
        db.query(Experiment)
        .order_by(Experiment.created_at.desc())
        .all()
    )


@router.post("/", response_model=ExperimentOut, status_code=201)
def create_experiment(body: ExperimentCreate, db: Session = Depends(get_db)):
    experiment = Experiment(
        name=body.name,
        description=body.description,
        dataset_id=body.dataset_id,
        analysis_type=body.analysis_type,
        parameters=body.parameters,
        status="running",
        git_commit=_git_commit(),
        environment_hash=_env_hash(),
        dataset_version=_dataset_version(body.dataset_id),
        container_image="policylab-worker:latest",
        python_version=sys.version.split()[0],
        started_at=datetime.utcnow(),
    )
    db.add(experiment)
    db.flush()  # get experiment.id

    job = Job(
        experiment_id=experiment.id,
        status="running",
        started_at=datetime.utcnow(),
        worker_id="ray-local-0",
    )
    db.add(job)
    db.commit()
    db.refresh(experiment)
    db.refresh(job)

    # Dispatch to Ray (or thread-pool fallback)
    future = submit_job(
        job_id=job.id,
        analysis_type=body.analysis_type,
        dataset_id=body.dataset_id,
        parameters=body.parameters,
    )
    _futures[job.id] = future
    record_job_submitted()

    return experiment


@router.get("/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.get("/{experiment_id}/artifacts", response_model=List[ArtifactOut])
def get_artifacts(experiment_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Artifact)
        .filter(Artifact.experiment_id == experiment_id)
        .all()
    )


# ---------------------------------------------------------------------------
# Job completion callback — called by the background monitor in main.py
# ---------------------------------------------------------------------------


def finalize_job(db: Session, job_id: str, result: Dict[str, Any]) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    now = datetime.utcnow()
    status = "completed" if result.get("success") else "failed"

    job.status = status
    job.logs = result.get("logs", "")
    job.error = result.get("error")
    job.peak_cpu_percent = result.get("peak_cpu", 0)
    job.peak_memory_mb = result.get("peak_memory_mb", 0)
    job.avg_cpu_percent = result.get("avg_cpu", 0)
    job.total_runtime_seconds = result.get("total_runtime_seconds", 0)
    job.completed_at = now

    # Persist per-step metrics
    for m in result.get("metrics", []):
        db.add(JobMetric(
            job_id=job.id,
            elapsed_seconds=m.get("elapsed_seconds", 0),
            cpu_percent=m.get("cpu_percent", 0),
            memory_mb=m.get("memory_mb", 0),
            gpu_memory_mb=m.get("gpu_memory_mb", 0),
            gpu_util_percent=m.get("gpu_util_percent", 0),
            throughput_rows_per_sec=m.get("throughput_rows_per_sec"),
        ))

    # Persist artifacts
    if result.get("artifacts"):
        db.add(Artifact(
            experiment_id=job.experiment_id,
            name="analysis_results",
            artifact_type="chart_data",
            content=result["artifacts"],
            size_bytes=len(json.dumps(result["artifacts"]).encode()),
        ))
        if result.get("reproducibility_manifest"):
            db.add(Artifact(
                experiment_id=job.experiment_id,
                name="reproducibility_manifest",
                artifact_type="manifest",
                content=result["reproducibility_manifest"],
                size_bytes=len(json.dumps(result["reproducibility_manifest"]).encode()),
            ))

    # Update parent experiment
    exp = db.query(Experiment).filter(Experiment.id == job.experiment_id).first()
    if exp:
        exp.status = status
        exp.completed_at = now

    db.commit()
