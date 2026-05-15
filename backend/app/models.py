import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    source = Column(String)
    category = Column(String)
    size_bytes = Column(Integer)
    row_count = Column(Integer)
    columns = Column(JSON)
    schema_info = Column(JSON)
    tags = Column(JSON)
    years_available = Column(JSON)
    geographic_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiments = relationship("Experiment", back_populates="dataset")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    dataset_id = Column(String, ForeignKey("datasets.id"))
    analysis_type = Column(String, nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(String, default="pending")  # pending | running | completed | failed

    # Reproducibility manifest
    git_commit = Column(String)
    environment_hash = Column(String)
    dataset_version = Column(String)
    container_image = Column(String)
    python_version = Column(String)
    dependencies_snapshot = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_by = Column(String, default="researcher")

    dataset = relationship("Dataset", back_populates="experiments")
    jobs = relationship("Job", back_populates="experiment", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="experiment", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=_uuid)
    experiment_id = Column(String, ForeignKey("experiments.id"))
    worker_id = Column(String)
    status = Column(String, default="pending")  # pending | running | completed | failed
    logs = Column(Text, default="")
    error = Column(Text)

    peak_cpu_percent = Column(Float)
    peak_memory_mb = Column(Float)
    avg_cpu_percent = Column(Float)
    total_runtime_seconds = Column(Float)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    experiment = relationship("Experiment", back_populates="jobs")
    metrics = relationship("JobMetric", back_populates="job", cascade="all, delete-orphan")


class JobMetric(Base):
    __tablename__ = "job_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    elapsed_seconds = Column(Float)
    cpu_percent = Column(Float)
    memory_mb = Column(Float)
    gpu_memory_mb = Column(Float, default=0.0)
    gpu_util_percent = Column(Float, default=0.0)
    throughput_rows_per_sec = Column(Float)

    job = relationship("Job", back_populates="metrics")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=_uuid)
    experiment_id = Column(String, ForeignKey("experiments.id"))
    name = Column(String)
    artifact_type = Column(String)  # chart_data | summary | csv_preview
    content = Column(JSON)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="artifacts")
