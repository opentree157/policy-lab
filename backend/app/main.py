"""
PolicyLab API — FastAPI application entry point.

Startup sequence:
  1. Create DB tables (SQLAlchemy create_all)
  2. Seed dataset catalog if empty
  3. Initialise Ray (local mode)
  4. Launch background job-monitor coroutine
"""

import asyncio
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Dataset
from app.routers import datasets, experiments, jobs, metrics
from app.seeds import DATASETS
from worker.runner import init_ray

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("policylab")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PolicyLab API",
    description="Cloud-based reproducible research platform for public policy datasets.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router, prefix="/api/v1")
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup():
    _create_tables()
    _seed_datasets()
    init_ray()
    asyncio.create_task(_job_monitor())
    log.info("PolicyLab API ready — env=%s", settings.app_env)


def _create_tables():
    Base.metadata.create_all(bind=engine)
    log.info("Database tables ready")


def _seed_datasets():
    db: Session = SessionLocal()
    try:
        if db.query(Dataset).count() == 0:
            for ds_data in DATASETS:
                db.add(Dataset(**ds_data))
            db.commit()
            log.info("Seeded %d datasets", len(DATASETS))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Background job monitor
# ---------------------------------------------------------------------------


async def _job_monitor():
    """Poll Ray every 2 s for completed jobs and update the database."""
    from app.routers.experiments import _futures, finalize_job
    from worker.runner import poll_job
    from app.routers.metrics import record_job_finished

    while True:
        await asyncio.sleep(2)
        if not _futures:
            continue

        db: Session = SessionLocal()
        try:
            done_ids = []
            for job_id, future in list(_futures.items()):
                result = poll_job(future, timeout=0)
                if result is not None:
                    log.info(
                        "Job %s finished — success=%s runtime=%.1fs",
                        job_id,
                        result.get("success"),
                        result.get("total_runtime_seconds", 0),
                    )
                    finalize_job(db, job_id, result)
                    record_job_finished(
                        "completed" if result.get("success") else "failed",
                        result.get("total_runtime_seconds", 0),
                    )
                    done_ids.append(job_id)
        except Exception as exc:
            log.exception("Job monitor error: %s", exc)
        finally:
            for jid in done_ids:
                _futures.pop(jid, None)
            db.close()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
