import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.analytics import CleaningOperation, CleaningPreviewResponse
from backend.app.services.cleaning_service import CleaningService

logger = logging.getLogger("insightiq.routes.cleaning")
router = APIRouter(prefix="/api/datasets", tags=["Data Cleaning"])


@router.post("/{dataset_id}/clean/preview", response_model=CleaningPreviewResponse)
def preview_clean_dataset(
    dataset_id: int,
    operations: CleaningOperation,
    db: Session = Depends(get_db)
):
    return CleaningService.preview_clean(dataset_id, operations, db)


@router.post("/{dataset_id}/clean")
def execute_clean_dataset(
    dataset_id: int,
    operations: CleaningOperation,
    db: Session = Depends(get_db)
):
    return CleaningService.execute_clean(dataset_id, operations, db)
