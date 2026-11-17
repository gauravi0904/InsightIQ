from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ClusteringRequest(BaseModel):
    features: List[str] = Field(..., min_length=2)
    n_clusters: int = Field(default=3, ge=2, le=10)


class ClusteringResponse(BaseModel):
    n_clusters: int
    features: List[str]
    total_records: int
    cluster_counts: Dict[str, int]
    cluster_centers: List[Dict[str, float]]
    silhouette_score: Optional[float] = None
    explanation: str
    figure_json: Optional[str] = None
    sample_rows: List[Dict[str, Any]]


class AnomalyRequest(BaseModel):
    features: List[str] = Field(..., min_length=1)
    contamination: float = Field(default=0.05, gt=0.0, le=0.5)


class AnomalyResponse(BaseModel):
    features: List[str]
    total_records: int
    contamination: float
    anomaly_count: int
    normal_count: int
    anomaly_percentage: float
    explanation: str
    figure_json: Optional[str] = None
    sample_anomalies: List[Dict[str, Any]]


class PredictionRequest(BaseModel):
    target_column: str
    feature_columns: List[str] = Field(..., min_length=1)
    test_size: float = Field(default=0.2, gt=0.05, lt=0.5)


class PredictionResponse(BaseModel):
    target_column: str
    feature_columns: List[str]
    train_size: int
    test_size: int
    mae: float
    rmse: float
    r2: float
    coefficients: Dict[str, float]
    intercept: float
    sample_predictions: List[Dict[str, Any]]
    figure_json: Optional[str] = None
    explanation: str
