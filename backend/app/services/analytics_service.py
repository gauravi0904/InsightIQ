import logging
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.schemas.analytics import (
    DatasetStatisticsResponse,
    NumericalStats,
    CategoricalStats
)
from backend.app.services.dataset_service import DatasetService

logger = logging.getLogger("insightiq.analytics_service")


class AnalyticsService:

    @classmethod
    def compute_statistics(cls, dataset_id: int, db: Session) -> DatasetStatisticsResponse:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)

        numerical_stats_list: List[NumericalStats] = []
        categorical_stats_list: List[CategoricalStats] = []

        # 1. Numerical statistics
        num_cols = df.select_dtypes(include=["number"]).columns
        for col in num_cols:
            series = df[col].dropna()
            missing_count = int(df[col].isnull().sum())
            unique_count = int(df[col].nunique(dropna=True))

            if len(series) == 0:
                stats = NumericalStats(
                    column=col,
                    count=0,
                    mean=None,
                    std=None,
                    min=None,
                    q25=None,
                    median=None,
                    q75=None,
                    max=None,
                    missing_count=missing_count,
                    unique_count=unique_count
                )
            else:
                stats = NumericalStats(
                    column=col,
                    count=int(len(series)),
                    mean=round(float(series.mean()), 4),
                    std=round(float(series.std()), 4) if len(series) > 1 else 0.0,
                    min=round(float(series.min()), 4),
                    q25=round(float(series.quantile(0.25)), 4),
                    median=round(float(series.median()), 4),
                    q75=round(float(series.quantile(0.75)), 4),
                    max=round(float(series.max()), 4),
                    missing_count=missing_count,
                    unique_count=unique_count
                )
            numerical_stats_list.append(stats)

        # 2. Categorical statistics
        cat_cols = df.select_dtypes(include=["object", "category", "string", "bool"]).columns
        for col in cat_cols:
            series = df[col].dropna()
            missing_count = int(df[col].isnull().sum())
            unique_count = int(df[col].nunique(dropna=True))

            # Top 10 frequent values
            top_val_counts = series.value_counts().head(10).to_dict()
            # Convert keys to str and counts to int
            clean_top_vals = {str(k): int(v) for k, v in top_val_counts.items()}

            categorical_stats_list.append(CategoricalStats(
                column=col,
                count=int(len(series)),
                unique_count=unique_count,
                top_values=clean_top_vals,
                missing_count=missing_count
            ))

        # 3. Correlation matrix for numerical columns (if at least 2 numerical columns)
        corr_matrix: Optional[Dict[str, Dict[str, Optional[float]]]] = None
        if len(num_cols) >= 2:
            try:
                corr_df = df[num_cols].corr()
                corr_dict = {}
                for r_col in corr_df.index:
                    corr_dict[r_col] = {}
                    for c_col in corr_df.columns:
                        val = corr_df.loc[r_col, c_col]
                        corr_dict[r_col][c_col] = round(float(val), 4) if not pd.isna(val) else None
                corr_matrix = corr_dict
            except Exception as e:
                logger.warning("Could not calculate correlation matrix: %s", e)
                corr_matrix = None

        return DatasetStatisticsResponse(
            dataset_id=dataset.id,
            numerical_stats=numerical_stats_list,
            categorical_stats=categorical_stats_list,
            correlation_matrix=corr_matrix
        )
