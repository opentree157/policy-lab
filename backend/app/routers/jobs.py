from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, JobMetric
from app.schemas import JobMetricOut, JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/logs", response_class=PlainTextResponse)
def get_logs(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.logs or ""


@router.get("/{job_id}/metrics", response_model=List[JobMetricOut])
def get_metrics(job_id: str, db: Session = Depends(get_db)):
    return (
        db.query(JobMetric)
        .filter(JobMetric.job_id == job_id)
        .order_by(JobMetric.elapsed_seconds)
        .all()
    )
