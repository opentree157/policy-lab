from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    source: str
    category: str
    size_bytes: int
    row_count: int
    columns: List[str]
    tags: List[str]
    years_available: List[int]
    geographic_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentCreate(BaseModel):
    name: str
    description: str = ""
    dataset_id: str
    analysis_type: str
    parameters: Dict[str, Any] = {}


class JobOut(BaseModel):
    id: str
    experiment_id: str
    worker_id: Optional[str]
    status: str
    logs: str
    error: Optional[str]
    peak_cpu_percent: Optional[float]
    peak_memory_mb: Optional[float]
    avg_cpu_percent: Optional[float]
    total_runtime_seconds: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class JobMetricOut(BaseModel):
    elapsed_seconds: float
    cpu_percent: float
    memory_mb: float
    gpu_memory_mb: float
    gpu_util_percent: float
    throughput_rows_per_sec: Optional[float]

    model_config = {"from_attributes": True}


class ArtifactOut(BaseModel):
    id: str
    experiment_id: str
    name: str
    artifact_type: str
    content: Optional[Any]
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    dataset_id: str
    analysis_type: str
    parameters: Dict[str, Any]
    status: str
    git_commit: Optional[str]
    environment_hash: Optional[str]
    dataset_version: Optional[str]
    container_image: Optional[str]
    python_version: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: str
    jobs: List[JobOut] = []
    artifacts: List[ArtifactOut] = []

    model_config = {"from_attributes": True}
