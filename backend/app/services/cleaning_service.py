import uuid
import json
import logging
from typing import Dict, Any, Tuple, List
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.models.dataset import Dataset
from backend.app.models.analysis import AnalysisHistory
from backend.app.schemas.analytics import CleaningOperation, CleaningPreviewResponse
from backend.app.services.dataset_service import DatasetService

logger = logging.getLogger("insightiq.cleaning_service")


class CleaningService:

    @staticmethod
    def apply_operations(df: pd.DataFrame, operations: CleaningOperation) -> Tuple[pd.DataFrame, List[str]]:
        changes: List[str] = []
        cleaned_df = df.copy()

        # 1. Rename columns
        if operations.rename_columns:
            valid_renames = {}
            for old_col, new_col in operations.rename_columns.items():
                if old_col in cleaned_df.columns:
                    new_name_clean = new_col.strip()
                    if new_name_clean and new_name_clean != old_col:
                        valid_renames[old_col] = new_name_clean
            if valid_renames:
                cleaned_df = cleaned_df.rename(columns=valid_renames)
                changes.append(f"Renamed {len(valid_renames)} column(s): {', '.join(f'{k} -> {v}' for k, v in valid_renames.items())}")

        # 2. Convert supported types
        if operations.convert_types:
            for col, target_type in operations.convert_types.items():
                if col in cleaned_df.columns:
                    try:
                        if target_type == "int":
                            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce").round().astype("Int64")
                            changes.append(f"Converted column '{col}' to Integer.")
                        elif target_type == "float":
                            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce").astype(float)
                            changes.append(f"Converted column '{col}' to Float.")
                        elif target_type == "str":
                            cleaned_df[col] = cleaned_df[col].astype(str)
                            changes.append(f"Converted column '{col}' to String.")
                        elif target_type == "datetime":
                            cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors="coerce")
                            changes.append(f"Converted column '{col}' to Datetime.")
                    except Exception as e:
                        changes.append(f"Could not convert column '{col}' to {target_type}: {str(e)}")

        # 3. Remove duplicate rows
        if operations.remove_duplicates:
            dups_count = int(cleaned_df.duplicated().sum())
            if dups_count > 0:
                cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
                changes.append(f"Removed {dups_count} duplicate row(s).")
            else:
                changes.append("No duplicate rows found.")

        # 4. Fill missing numerical values
        if operations.fill_numeric in ["mean", "median"]:
            num_cols = cleaned_df.select_dtypes(include=["number"]).columns
            filled_cols = []
            for col in num_cols:
                missing_cnt = cleaned_df[col].isnull().sum()
                if missing_cnt > 0:
                    fill_val = cleaned_df[col].mean() if operations.fill_numeric == "mean" else cleaned_df[col].median()
                    cleaned_df[col] = cleaned_df[col].fillna(fill_val)
                    filled_cols.append(f"{col} ({missing_cnt} missing -> {operations.fill_numeric}={round(fill_val, 2)})")
            if filled_cols:
                changes.append(f"Filled numeric missing with {operations.fill_numeric}: {', '.join(filled_cols)}.")
            else:
                changes.append(f"No numeric missing values to fill with {operations.fill_numeric}.")

        # 5. Fill missing categorical values
        if operations.fill_categorical == "mode":
            cat_cols = cleaned_df.select_dtypes(include=["object", "category", "string"]).columns
            filled_cols = []
            for col in cat_cols:
                missing_cnt = cleaned_df[col].isnull().sum()
                if missing_cnt > 0:
                    modes = cleaned_df[col].mode()
                    if not modes.empty:
                        mode_val = modes[0]
                        cleaned_df[col] = cleaned_df[col].fillna(mode_val)
                        filled_cols.append(f"{col} ({missing_cnt} missing -> mode='{mode_val}')")
            if filled_cols:
                changes.append(f"Filled categorical missing with mode: {', '.join(filled_cols)}.")
            else:
                changes.append("No categorical missing values to fill with mode.")

        # 6. Drop missing rows
        if operations.drop_na:
            missing_rows = int(cleaned_df.isnull().any(axis=1).sum())
            if missing_rows > 0:
                cleaned_df = cleaned_df.dropna().reset_index(drop=True)
                changes.append(f"Dropped {missing_rows} row(s) containing missing values.")
            else:
                changes.append("No rows with missing values to drop.")

        if not changes:
            changes.append("No cleaning operations were selected or needed.")

        return cleaned_df, changes

    @classmethod
    def preview_clean(cls, dataset_id: int, operations: CleaningOperation, db: Session) -> CleaningPreviewResponse:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        original_df = DatasetService.load_dataframe(dataset)

        before_rows = int(original_df.shape[0])
        before_columns = int(original_df.shape[1])
        before_missing = int(original_df.isnull().sum().sum())
        before_duplicates = int(original_df.duplicated().sum())

        cleaned_df, changes = cls.apply_operations(original_df, operations)

        after_rows = int(cleaned_df.shape[0])
        after_columns = int(cleaned_df.shape[1])
        after_missing = int(cleaned_df.isnull().sum().sum())
        after_duplicates = int(cleaned_df.duplicated().sum())

        preview_records = cleaned_df.head(10).replace({float("nan"): None}).to_dict(orient="records")

        return CleaningPreviewResponse(
            before_rows=before_rows,
            before_columns=before_columns,
            before_missing=before_missing,
            before_duplicates=before_duplicates,
            after_rows=after_rows,
            after_columns=after_columns,
            after_missing=after_missing,
            after_duplicates=after_duplicates,
            changes_summary=changes,
            preview_rows=preview_records
        )

    @classmethod
    def execute_clean(cls, dataset_id: int, operations: CleaningOperation, db: Session) -> Dict[str, Any]:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        original_df = DatasetService.load_dataframe(dataset)

        cleaned_df, changes = cls.apply_operations(original_df, operations)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cleaning operations resulted in an empty dataset. Operation cancelled to prevent data loss."
            )

        # Decide whether to save as new dataset or save processed version
        if operations.save_as_new:
            new_name = (operations.new_dataset_name or f"{dataset.dataset_name}_cleaned").strip()
            new_filename = f"{uuid.uuid4().hex}_{new_name}.csv"
            save_path = settings.PROCESSED_DIR / new_filename
            cleaned_df.to_csv(save_path, index=False)

            new_dataset = Dataset(
                dataset_name=new_name,
                original_filename=f"{new_name}.csv",
                stored_filename=new_filename,
                file_type="csv",
                file_size=save_path.stat().st_size,
                row_count=int(cleaned_df.shape[0]),
                column_count=int(cleaned_df.shape[1]),
                processing_status="cleaned"
            )
            db.add(new_dataset)
            db.commit()
            db.refresh(new_dataset)
            result_dataset = new_dataset
        else:
            # Save to processed directory without overwriting original upload
            proc_filename = f"cleaned_{uuid.uuid4().hex[:8]}_{dataset.stored_filename.split('_', 1)[-1]}"
            if not proc_filename.endswith(".csv"):
                proc_filename = f"{Path(proc_filename).stem}.csv"
            save_path = settings.PROCESSED_DIR / proc_filename
            cleaned_df.to_csv(save_path, index=False)

            # Update dataset record
            dataset.stored_filename = proc_filename
            dataset.file_type = "csv"
            dataset.file_size = save_path.stat().st_size
            dataset.row_count = int(cleaned_df.shape[0])
            dataset.column_count = int(cleaned_df.shape[1])
            dataset.processing_status = "cleaned"
            db.commit()
            db.refresh(dataset)
            result_dataset = dataset

        # Record analysis history
        history = AnalysisHistory(
            dataset_id=result_dataset.id,
            analysis_type="cleaning",
            parameters=json.dumps(operations.model_dump()),
            result_summary=json.dumps({"changes": changes, "rows": result_dataset.row_count, "cols": result_dataset.column_count})
        )
        db.add(history)
        db.commit()

        return {
            "status": "success",
            "message": "Dataset successfully cleaned and saved.",
            "dataset_id": result_dataset.id,
            "dataset_name": result_dataset.dataset_name,
            "row_count": result_dataset.row_count,
            "column_count": result_dataset.column_count,
            "changes_summary": changes
        }
