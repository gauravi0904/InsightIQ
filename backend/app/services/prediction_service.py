import json
import logging
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.analysis import AnalysisHistory
from backend.app.schemas.ml import PredictionRequest, PredictionResponse
from backend.app.services.dataset_service import DatasetService

logger = logging.getLogger("insightiq.prediction_service")


class PredictionService:

    @classmethod
    def train_and_predict(cls, dataset_id: int, req: PredictionRequest, db: Session) -> PredictionResponse:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)

        target = req.target_column
        features = req.feature_columns

        # 1. Validation: column existence
        if target not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target}' does not exist in dataset."
            )

        if not features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one input feature column must be selected."
            )

        # 2. Prevent target leakage
        if target in features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target leakage detected: Target column '{target}' cannot be included in input features."
            )

        missing_feats = [f for f in features if f not in df.columns]
        if missing_feats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feature columns not found: {', '.join(missing_feats)}"
            )

        # 3. Check data types
        if not pd.api.types.is_numeric_dtype(df[target]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target}' is non-numeric ({df[target].dtype}). Linear regression requires a numerical continuous target."
            )

        for f in features:
            if not pd.api.types.is_numeric_dtype(df[f]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feature column '{f}' is non-numeric ({df[f].dtype})."
                )

        # 4. Clean missing values in chosen columns
        all_cols = features + [target]
        clean_df = df[all_cols].dropna()
        n_samples = len(clean_df)

        if n_samples < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset is not suitable for regression: only {n_samples} complete rows available (minimum 20 required)."
            )

        # 5. Check constant variance
        if clean_df[target].std() == 0 or clean_df[target].nunique() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target}' has zero variance (constant values). A model cannot learn from constant target."
            )

        constant_feats = [f for f in features if clean_df[f].nunique() <= 1]
        if constant_feats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feature column(s) {', '.join(constant_feats)} have zero variance. Remove them before training."
            )

        # 6. Train/Test split
        X = clean_df[features].values
        y = clean_df[target].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=req.test_size, random_state=42
        )

        if len(X_train) < 5 or len(X_test) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient rows after train/test split. Ensure dataset has enough observations."
            )

        # 7. Fit Linear Regression
        model = LinearRegression()
        model.fit(X_train, y_train)

        # 8. Evaluate
        y_pred = model.predict(X_test)

        mae = float(mean_absolute_error(y_test, y_pred))
        mse = float(mean_squared_error(y_test, y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_test, y_pred))

        coefs_dict = {f: round(float(c), 4) for f, c in zip(features, model.coef_)}
        intercept = round(float(model.intercept_), 4)

        # 9. Plot: Actual vs Predicted
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=y_test,
            y=y_pred,
            mode="markers",
            name="Predictions",
            marker=dict(color="#2563eb", size=8, opacity=0.8)
        ))
        # Add ideal 45-degree reference line
        min_val = float(min(y_test.min(), y_pred.min()))
        max_val = float(max(y_test.max(), y_pred.max()))
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode="lines",
            name="Ideal Fit (y = x)",
            line=dict(color="#ef4444", dash="dash")
        ))
        fig.update_layout(
            title=f"Actual vs Predicted: {target} (R² = {round(r2, 3)})",
            xaxis_title="Actual Values",
            yaxis_title="Predicted Values",
            template="plotly_white"
        )
        fig_json = fig.to_json()

        # 10. Sample predictions table
        sample_size = min(15, len(y_test))
        samples = []
        for i in range(sample_size):
            row_dict = {}
            for j, f in enumerate(features):
                row_dict[f] = round(float(X_test[i][j]), 2)
            row_dict[f"Actual_{target}"] = round(float(y_test[i]), 2)
            row_dict[f"Predicted_{target}"] = round(float(y_pred[i]), 2)
            row_dict["Absolute_Error"] = round(float(abs(y_test[i] - y_pred[i])), 2)
            samples.append(row_dict)

        explanation = (
            f"Linear Regression trained on {len(X_train)} samples and evaluated on {len(X_test)} test samples. "
            f"Model achieved R² = {round(r2, 4)}, MAE = {round(mae, 2)}, and RMSE = {round(rmse, 2)}. "
            f"Target: '{target}', Predictor features: {', '.join(features)}."
        )

        history = AnalysisHistory(
            dataset_id=dataset.id,
            analysis_type="prediction",
            parameters=json.dumps({"target": target, "features": features, "test_size": req.test_size}),
            result_summary=json.dumps({"r2": round(r2, 4), "mae": round(mae, 2), "rmse": round(rmse, 2)})
        )
        db.add(history)
        db.commit()

        return PredictionResponse(
            target_column=target,
            feature_columns=features,
            train_size=len(X_train),
            test_size=len(X_test),
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            r2=round(r2, 4),
            coefficients=coefs_dict,
            intercept=intercept,
            sample_predictions=samples,
            figure_json=fig_json,
            explanation=explanation
        )
