import json
import logging
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.analysis import AnalysisHistory
from backend.app.schemas.ml import AnomalyRequest, AnomalyResponse
from backend.app.services.dataset_service import DatasetService

logger = logging.getLogger("insightiq.anomaly_service")


class AnomalyService:

    @classmethod
    def detect_anomalies(cls, dataset_id: int, req: AnomalyRequest, db: Session) -> AnomalyResponse:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)

        # 1. Validation
        if len(req.features) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Anomaly detection requires at least 1 numerical feature."
            )

        missing_cols = [f for f in req.features if f not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Columns not found in dataset: {', '.join(missing_cols)}"
            )

        for f in req.features:
            if not pd.api.types.is_numeric_dtype(df[f]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feature '{f}' is not numerical (dtype: {df[f].dtype})."
                )

        clean_subset = df[req.features].dropna()
        n_samples = len(clean_subset)

        if n_samples < 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset is not suitable for anomaly detection because it contains only {n_samples} complete rows (minimum 15 required)."
            )

        # 2. Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=req.contamination,
            random_state=42,
            n_estimators=100
        )
        preds = iso_forest.fit_predict(clean_subset.values)
        # -1 = anomaly, 1 = normal
        is_anomaly = (preds == -1)

        anomaly_count = int(np.sum(is_anomaly))
        normal_count = int(np.sum(~is_anomaly))
        anomaly_pct = round((anomaly_count / max(n_samples, 1)) * 100, 2)

        # 3. Visualization
        plot_df = clean_subset.copy()
        plot_df["Status"] = np.where(is_anomaly, "Anomaly", "Normal")

        fig = None
        if len(req.features) == 1:
            plot_df["Index"] = plot_df.index
            fig = px.scatter(
                plot_df, x="Index", y=req.features[0],
                color="Status",
                color_discrete_map={"Normal": "#2563eb", "Anomaly": "#ef4444"},
                title=f"Anomaly Detection on {req.features[0]} (Contamination: {req.contamination})",
                template="plotly_white"
            )
        elif len(req.features) == 2:
            fig = px.scatter(
                plot_df, x=req.features[0], y=req.features[1],
                color="Status",
                color_discrete_map={"Normal": "#2563eb", "Anomaly": "#ef4444"},
                title=f"Anomaly Detection on {req.features[0]} vs {req.features[1]}",
                template="plotly_white"
            )
        else:
            # Multi-feature PCA projection
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(clean_subset.values)
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X_scaled)
            plot_df["PCA 1"] = coords[:, 0]
            plot_df["PCA 2"] = coords[:, 1]
            fig = px.scatter(
                plot_df, x="PCA 1", y="PCA 2",
                color="Status",
                color_discrete_map={"Normal": "#2563eb", "Anomaly": "#ef4444"},
                title="Anomaly Detection (PCA 2D Projection)",
                template="plotly_white"
            )

        fig_json = fig.to_json() if fig else None

        # Extract sample anomalous rows
        full_sub = df.loc[clean_subset.index].copy()
        full_sub["anomaly_flag"] = is_anomaly
        anomalies_df = full_sub[full_sub["anomaly_flag"]].drop(columns=["anomaly_flag"])
        sample_anomalies = anomalies_df.head(15).replace({float("nan"): None}).to_dict(orient="records")

        explanation = (
            f"Isolation Forest identified {anomaly_count} anomalous records ({anomaly_pct}%) and "
            f"{normal_count} normal records from {n_samples} total instances using {len(req.features)} feature(s). "
            "Note: An anomaly is an unusual observation according to feature density and distance. "
            "It is not automatically an error, fraud, or defect without domain-specific investigation."
        )

        history = AnalysisHistory(
            dataset_id=dataset.id,
            analysis_type="anomaly",
            parameters=json.dumps({"features": req.features, "contamination": req.contamination}),
            result_summary=json.dumps({"anomalies": anomaly_count, "normal": normal_count, "percentage": anomaly_pct})
        )
        db.add(history)
        db.commit()

        return AnomalyResponse(
            features=req.features,
            total_records=n_samples,
            contamination=req.contamination,
            anomaly_count=anomaly_count,
            normal_count=normal_count,
            anomaly_percentage=anomaly_pct,
            explanation=explanation,
            figure_json=fig_json,
            sample_anomalies=sample_anomalies
        )
