import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.ml import (
    ClusteringRequest,
    ClusteringResponse,
    AnomalyRequest,
    AnomalyResponse,
    PredictionRequest,
    PredictionResponse
)
from backend.app.services.clustering_service import ClusteringService
from backend.app.services.anomaly_service import AnomalyService
from backend.app.services.prediction_service import PredictionService

logger = logging.getLogger("insightiq.routes.ml")
router = APIRouter(prefix="/api/datasets", tags=["Machine Learning Studio"])


@router.post("/{dataset_id}/ml/clustering", response_model=ClusteringResponse)
def run_clustering(
    dataset_id: int,
    req: ClusteringRequest,
    db: Session = Depends(get_db)
):
    return ClusteringService.run_kmeans(dataset_id, req, db)


@router.post("/{dataset_id}/ml/anomaly", response_model=AnomalyResponse)
def run_anomaly_detection(
    dataset_id: int,
    req: AnomalyRequest,
    db: Session = Depends(get_db)
):
    return AnomalyService.detect_anomalies(dataset_id, req, db)


@router.post("/{dataset_id}/ml/prediction", response_model=PredictionResponse)
def run_prediction(
    dataset_id: int,
    req: PredictionRequest,
    db: Session = Depends(get_db)
):
    return PredictionService.train_and_predict(dataset_id, req, db)
