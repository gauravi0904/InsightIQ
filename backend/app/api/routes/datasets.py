import logging
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.dataset import (
    DatasetResponse,
    DatasetUploadResponse,
    DatasetPreviewResponse,
    DatasetSchemaResponse
)
from backend.app.schemas.analytics import DatasetStatisticsResponse
from backend.app.services.dataset_service import DatasetService
from backend.app.services.analytics_service import AnalyticsService

logger = logging.getLogger("insightiq.routes.datasets")
router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    dataset = DatasetService.save_uploaded_file(file, db)
    return DatasetUploadResponse(
        id=dataset.id,
        dataset_name=dataset.dataset_name,
        original_filename=dataset.original_filename,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        processing_status=dataset.processing_status,
        message="Dataset uploaded and registered successfully."
    )


@router.get("", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    return DatasetService.list_datasets(db)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    return DatasetService.get_dataset_by_id(dataset_id, db)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    return DatasetService.delete_dataset(dataset_id, db)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(dataset_id: int, db: Session = Depends(get_db)):
    return DatasetService.get_preview(dataset_id, db)


@router.get("/{dataset_id}/schema", response_model=DatasetSchemaResponse)
def get_dataset_schema(dataset_id: int, db: Session = Depends(get_db)):
    return DatasetService.get_schema(dataset_id, db)


@router.get("/{dataset_id}/statistics", response_model=DatasetStatisticsResponse)
def get_dataset_statistics(dataset_id: int, db: Session = Depends(get_db)):
    return AnalyticsService.compute_statistics(dataset_id, db)
