from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset
from app.schemas import DatasetOut
from app.seeds import ANALYSIS_TEMPLATES
from worker.analyses.world_bank import AVAILABLE_INDICATORS

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.name).all()


@router.get("/analysis-templates", response_model=Dict[str, Any])
def list_analysis_templates():
    return ANALYSIS_TEMPLATES


@router.get("/wb-indicators", response_model=Dict[str, Any])
def list_wb_indicators():
    """Return the full curated World Bank indicator catalog."""
    return AVAILABLE_INDICATORS


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds
