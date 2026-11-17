import io
import json
import logging
from typing import Dict, Any
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from backend.app.core.config import settings
from backend.app.models.dataset import Dataset
from backend.app.models.analysis import AnalysisHistory
from backend.app.services.dataset_service import DatasetService
from backend.app.services.analytics_service import AnalyticsService

logger = logging.getLogger("insightiq.report_service")


class ReportService:

    @classmethod
    def generate_report_json(cls, dataset_id: int, db: Session) -> Dict[str, Any]:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)
        stats = AnalyticsService.compute_statistics(dataset_id, db)

        # Retrieve analysis history
        history_records = db.query(AnalysisHistory).filter(
            AnalysisHistory.dataset_id == dataset_id
        ).order_by(AnalysisHistory.created_at.desc()).all()

        history_list = []
        for h in history_records:
            history_list.append({
                "id": h.id,
                "analysis_type": h.analysis_type,
                "parameters": json.loads(h.parameters) if h.parameters else {},
                "result_summary": json.loads(h.result_summary) if h.result_summary else {},
                "created_at": h.created_at.isoformat() if h.created_at else None
            })

        missing_counts = df.isnull().sum().to_dict()
        missing_total = int(df.isnull().sum().sum())
        duplicate_total = int(df.duplicated().sum())

        return {
            "dataset": {
                "id": dataset.id,
                "name": dataset.dataset_name,
                "original_filename": dataset.original_filename,
                "file_type": dataset.file_type,
                "file_size_bytes": dataset.file_size,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "status": dataset.processing_status,
                "upload_date": dataset.upload_date.isoformat() if dataset.upload_date else None
            },
            "data_quality": {
                "total_missing_cells": missing_total,
                "duplicate_rows": duplicate_total,
                "missing_by_column": {k: int(v) for k, v in missing_counts.items()}
            },
            "numerical_statistics": [s.model_dump() for s in stats.numerical_stats],
            "categorical_statistics": [s.model_dump() for s in stats.categorical_stats],
            "analysis_history": history_list
        }

    @classmethod
    def export_dataset_file(cls, dataset_id: int, format_type: str, db: Session):
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)

        fmt = format_type.lower()
        if fmt == "csv":
            stream = io.StringIO()
            df.to_csv(stream, index=False)
            response = StreamingResponse(
                iter([stream.getvalue()]),
                media_type="text/csv"
            )
            response.headers["Content-Disposition"] = f"attachment; filename={dataset.dataset_name}_export.csv"
            return response

        elif fmt in ["xlsx", "excel"]:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Sheet 1: Data
                df.to_excel(writer, sheet_name="Data", index=False)

                # Sheet 2: Summary Stats
                stats = AnalyticsService.compute_statistics(dataset_id, db)
                if stats.numerical_stats:
                    num_df = pd.DataFrame([s.model_dump() for s in stats.numerical_stats])
                    num_df.to_excel(writer, sheet_name="Numerical Stats", index=False)
                if stats.categorical_stats:
                    cat_rows = []
                    for c in stats.categorical_stats:
                        cat_rows.append({
                            "column": c.column,
                            "count": c.count,
                            "unique_count": c.unique_count,
                            "missing_count": c.missing_count,
                            "top_values": str(c.top_values)
                        })
                    cat_df = pd.DataFrame(cat_rows)
                    cat_df.to_excel(writer, sheet_name="Categorical Stats", index=False)

            output.seek(0)
            response = StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response.headers["Content-Disposition"] = f"attachment; filename={dataset.dataset_name}_report.xlsx"
            return response

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format '{format_type}'. Use 'csv' or 'xlsx'."
            )
