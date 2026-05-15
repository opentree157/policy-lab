import time
from typing import Any, Dict

import psutil
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from fastapi.responses import Response

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Prometheus metrics
_jobs_submitted = Counter("policylab_jobs_submitted_total", "Total jobs submitted")
_jobs_completed = Counter("policylab_jobs_completed_total", "Total jobs completed", ["status"])
_job_duration = Histogram(
    "policylab_job_duration_seconds",
    "Job execution duration",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)
_active_jobs = Gauge("policylab_active_jobs", "Currently running jobs")
_cpu_usage = Gauge("policylab_host_cpu_percent", "Host CPU utilisation percent")
_memory_usage = Gauge("policylab_host_memory_mb", "Host memory used (MB)")

_start_time = time.time()


def record_job_submitted():
    _jobs_submitted.inc()
    _active_jobs.inc()


def record_job_finished(status: str, duration_seconds: float):
    _jobs_completed.labels(status=status).inc()
    _job_duration.observe(duration_seconds)
    _active_jobs.dec()


@router.get("/system", response_model=Dict[str, Any])
def system_metrics():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    _cpu_usage.set(cpu)
    _memory_usage.set(mem.used / 1_048_576)
    return {
        "cpu_percent": cpu,
        "cpu_count": psutil.cpu_count(),
        "memory_used_mb": round(mem.used / 1_048_576, 1),
        "memory_total_mb": round(mem.total / 1_048_576, 1),
        "memory_percent": mem.percent,
        "disk_used_gb": round(disk.used / 1_073_741_824, 2),
        "disk_total_gb": round(disk.total / 1_073_741_824, 2),
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


@router.get("/prometheus")
def prometheus_metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
