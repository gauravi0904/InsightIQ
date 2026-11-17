import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.analytics import (
    DatasetStatisticsResponse,
    VisualizationRequest,
    VisualizationResponse
)
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.visualization_service import VisualizationService

logger = logging.getLogger("insightiq.routes.analytics")
router = APIRouter(prefix="/api/datasets", tags=["Analytics & Visualization"])


@router.post("/{dataset_id}/analytics", response_model=DatasetStatisticsResponse)
def compute_analytics(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    return AnalyticsService.compute_statistics(dataset_id, db)


@router.post("/{dataset_id}/visualization", response_model=VisualizationResponse)
def create_visualization(
    dataset_id: int,
    req: VisualizationRequest,
    db: Session = Depends(get_db)
):
    return VisualizationService.generate_chart(dataset_id, req, db)
