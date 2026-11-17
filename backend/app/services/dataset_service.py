import uuid
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import settings
from backend.app.models.dataset import Dataset
from backend.app.models.analysis import AnalysisHistory
from backend.app.schemas.dataset import DatasetPreviewResponse, DatasetSchemaResponse, ColumnDetail

logger = logging.getLogger("insightiq.dataset_service")


def sanitize_filename(filename: str) -> str:
    # Keep only alphanumeric, dash, underscore, and dot
    clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
    return clean


def read_file_to_dataframe(file_path: Path, extension: str) -> pd.DataFrame:
    ext = extension.lower()
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1")
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
        return df
    except Exception as exc:
        logger.error("Failed to parse file at %s: %s", file_path, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse dataset: {str(exc)}"
        )


class DatasetService:

    @staticmethod
    def get_dataset_by_id(dataset_id: int, db: Session) -> Dataset:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID {dataset_id} was not found."
            )
        return dataset

    @staticmethod
    def list_datasets(db: Session) -> List[Dataset]:
        return db.query(Dataset).order_by(Dataset.created_at.desc()).all()

    @staticmethod
    def save_uploaded_file(upload_file: UploadFile, db: Session) -> Dataset:
        original_name = upload_file.filename or "uploaded_dataset.csv"
        safe_name = sanitize_filename(original_name)
        ext = Path(safe_name).suffix.lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        unique_filename = f"{uuid.uuid4().hex}_{safe_name}"
        destination_path = settings.UPLOAD_DIR / unique_filename

        # Stream file to disk and validate size
        total_bytes = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        try:
            with open(destination_path, "wb") as f_out:
                while chunk := upload_file.file.read(1024 * 64):
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        destination_path.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    f_out.write(chunk)
        except HTTPException:
            raise
        except Exception as exc:
            destination_path.unlink(missing_ok=True)
            logger.error("Error writing uploaded file: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file."
            )

        if total_bytes == 0:
            destination_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        # Parse with Pandas to inspect metadata
        try:
            df = read_file_to_dataframe(destination_path, ext)
        except Exception:
            destination_path.unlink(missing_ok=True)
            raise

        if df.empty or len(df.columns) == 0:
            destination_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset contains no usable rows or columns."
            )

        dataset_record = Dataset(
            dataset_name=Path(original_name).stem,
            original_filename=original_name,
            stored_filename=unique_filename,
            file_type=ext.lstrip("."),
            file_size=total_bytes,
            row_count=int(df.shape[0]),
            column_count=int(df.shape[1]),
            processing_status="ready"
        )
        db.add(dataset_record)
        db.commit()
        db.refresh(dataset_record)

        logger.info(
            "Saved dataset ID %s ('%s', %s rows, %s cols)",
            dataset_record.id, dataset_record.dataset_name, df.shape[0], df.shape[1]
        )
        return dataset_record

    @staticmethod
    def load_dataframe(dataset: Dataset) -> pd.DataFrame:
        file_path = settings.UPLOAD_DIR / dataset.stored_filename
        if not file_path.exists():
            # Check processed dir
            alt_path = settings.PROCESSED_DIR / dataset.stored_filename
            if alt_path.exists():
                file_path = alt_path
            else:
                logger.error("File for dataset ID %s not found on disk at %s", dataset.id, file_path)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data file '{dataset.stored_filename}' not found on storage."
                )
        return read_file_to_dataframe(file_path, f".{dataset.file_type}")

    @classmethod
    def get_preview(cls, dataset_id: int, db: Session) -> DatasetPreviewResponse:
        dataset = cls.get_dataset_by_id(dataset_id, db)
        df = cls.load_dataframe(dataset)

        dtypes_map = {col: str(dtype) for col, dtype in df.dtypes.items()}
        missing_counts = df.isnull().sum().to_dict()
        missing_percentages = {col: round(float(cnt) / max(len(df), 1) * 100, 2) for col, cnt in missing_counts.items()}
        duplicate_count = int(df.duplicated().sum())
        unique_counts = {col: int(df[col].nunique(dropna=True)) for col in df.columns}

        # Count dtype categories
        dtype_summary = {"numerical": 0, "categorical": 0, "datetime": 0, "other": 0}
        for dtype_str in dtypes_map.values():
            if "int" in dtype_str or "float" in dtype_str:
                dtype_summary["numerical"] += 1
            elif "object" in dtype_str or "string" in dtype_str or "category" in dtype_str:
                dtype_summary["categorical"] += 1
            elif "datetime" in dtype_str:
                dtype_summary["datetime"] += 1
            else:
                dtype_summary["other"] += 1

        # Replace NaN with None for JSON serialization
        head_records = df.head(10).replace({float("nan"): None}).to_dict(orient="records")
        tail_records = df.tail(10).replace({float("nan"): None}).to_dict(orient="records")

        return DatasetPreviewResponse(
            dataset_id=dataset.id,
            dataset_name=dataset.dataset_name,
            row_count=int(df.shape[0]),
            column_count=int(df.shape[1]),
            columns=list(df.columns),
            dtypes=dtypes_map,
            missing_counts={col: int(val) for col, val in missing_counts.items()},
            missing_percentages=missing_percentages,
            duplicate_count=duplicate_count,
            unique_counts=unique_counts,
            head=head_records,
            tail=tail_records,
            total_missing_cells=int(df.isnull().sum().sum()),
            data_types_summary=dtype_summary
        )

    @classmethod
    def get_schema(cls, dataset_id: int, db: Session) -> DatasetSchemaResponse:
        dataset = cls.get_dataset_by_id(dataset_id, db)
        df = cls.load_dataframe(dataset)

        columns_info: List[ColumnDetail] = []
        for col in df.columns:
            series = df[col]
            missing_count = int(series.isnull().sum())
            missing_pct = round(missing_count / max(len(df), 1) * 100, 2)
            unique_cnt = int(series.nunique(dropna=True))
            # Sample non-null values
            sample_vals = series.dropna().head(3).tolist()
            # Clean samples for json serialization
            clean_samples = [None if pd.isna(v) else (v if not hasattr(v, "item") else v.item()) for v in sample_vals]

            columns_info.append(ColumnDetail(
                name=col,
                dtype=str(series.dtype),
                missing_count=missing_count,
                missing_percentage=missing_pct,
                unique_count=unique_cnt,
                sample_values=clean_samples
            ))

        return DatasetSchemaResponse(
            dataset_id=dataset.id,
            columns=columns_info,
            total_rows=int(df.shape[0]),
            total_columns=int(df.shape[1])
        )

    @classmethod
    def delete_dataset(cls, dataset_id: int, db: Session) -> dict:
        dataset = cls.get_dataset_by_id(dataset_id, db)

        # Delete physical file from uploads
        file_path = settings.UPLOAD_DIR / dataset.stored_filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning("Failed to delete upload file %s: %s", file_path, e)

        # Also check processed dir
        processed_path = settings.PROCESSED_DIR / dataset.stored_filename
        if processed_path.exists():
            try:
                processed_path.unlink()
            except Exception as e:
                logger.warning("Failed to delete processed file %s: %s", processed_path, e)

        # Delete database record (cascade deletes analyses)
        db.query(AnalysisHistory).filter(AnalysisHistory.dataset_id == dataset_id).delete()
        db.delete(dataset)
        db.commit()

        logger.info("Deleted dataset ID %s and associated files.", dataset_id)
        return {"status": "success", "message": f"Dataset '{dataset.dataset_name}' deleted successfully."}
