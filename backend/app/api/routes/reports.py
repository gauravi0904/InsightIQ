import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.report_service import ReportService

logger = logging.getLogger("insightiq.routes.reports")
router = APIRouter(prefix="/api/datasets", tags=["Reports & Exports"])


@router.get("/{dataset_id}/report")
def get_dataset_report(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    return ReportService.generate_report_json(dataset_id, db)


@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: int,
    format: str = Query("csv", description="Format to download: 'csv' or 'xlsx'"),
    db: Session = Depends(get_db)
):
    return ReportService.export_dataset_file(dataset_id, format, db)
