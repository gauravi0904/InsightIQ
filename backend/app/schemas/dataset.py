from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_name: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    row_count: int
    column_count: int
    upload_date: datetime
    processing_status: str
    created_at: datetime
    updated_at: datetime


class DatasetUploadResponse(BaseModel):
    id: int
    dataset_name: str
    original_filename: str
    row_count: int
    column_count: int
    processing_status: str
    message: str


class ColumnDetail(BaseModel):
    name: str
    dtype: str
    missing_count: int
    missing_percentage: float
    unique_count: int
    sample_values: List[Any] = Field(default_factory=list)


class DatasetPreviewResponse(BaseModel):
    dataset_id: int
    dataset_name: str
    row_count: int
    column_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    missing_counts: Dict[str, int]
    missing_percentages: Dict[str, float]
    duplicate_count: int
    unique_counts: Dict[str, int]
    head: List[Dict[str, Any]]
    tail: List[Dict[str, Any]]
    total_missing_cells: int
    data_types_summary: Dict[str, int]


class DatasetSchemaResponse(BaseModel):
    dataset_id: int
    columns: List[ColumnDetail]
    total_rows: int
    total_columns: int
