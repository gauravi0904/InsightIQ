from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NumericalStats(BaseModel):
    column: str
    count: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    q25: Optional[float] = None
    median: Optional[float] = None
    q75: Optional[float] = None
    max: Optional[float] = None
    missing_count: int
    unique_count: int


class CategoricalStats(BaseModel):
    column: str
    count: int
    unique_count: int
    top_values: Dict[str, int]
    missing_count: int


class DatasetStatisticsResponse(BaseModel):
    dataset_id: int
    numerical_stats: List[NumericalStats]
    categorical_stats: List[CategoricalStats]
    correlation_matrix: Optional[Dict[str, Dict[str, Optional[float]]]] = None


class VisualizationRequest(BaseModel):
    chart_type: str = Field(..., description="bar, line, histogram, scatter, pie, box")
    x_column: str
    y_column: Optional[str] = None
    group_column: Optional[str] = None
    title: Optional[str] = None


class VisualizationResponse(BaseModel):
    chart_type: str
    figure_json: str
    message: str


class CleaningOperation(BaseModel):
    remove_duplicates: bool = False
    fill_numeric: Optional[str] = None  # "mean", "median", None
    fill_categorical: Optional[str] = None  # "mode", None
    drop_na: bool = False
    rename_columns: Optional[Dict[str, str]] = None
    convert_types: Optional[Dict[str, str]] = None  # {col_name: "int" | "float" | "str" | "datetime"}
    save_as_new: bool = False
    new_dataset_name: Optional[str] = None


class CleaningPreviewResponse(BaseModel):
    before_rows: int
    before_columns: int
    before_missing: int
    before_duplicates: int
    after_rows: int
    after_columns: int
    after_missing: int
    after_duplicates: int
    changes_summary: List[str]
    preview_rows: List[Dict[str, Any]]
