import json
import logging
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.analysis import AnalysisHistory
from backend.app.schemas.ml import ClusteringRequest, ClusteringResponse
from backend.app.services.dataset_service import DatasetService

logger = logging.getLogger("insightiq.clustering_service")


class ClusteringService:

    @classmethod
    def run_kmeans(cls, dataset_id: int, req: ClusteringRequest, db: Session) -> ClusteringResponse:
        dataset = DatasetService.get_dataset_by_id(dataset_id, db)
        df = DatasetService.load_dataframe(dataset)

        # 1. Validation: features
        if len(req.features) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer segmentation requires at least 2 numerical features."
            )

        missing_cols = [f for f in req.features if f not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following feature columns were not found in the dataset: {', '.join(missing_cols)}"
            )

        # Validate numerical types
        for f in req.features:
            if not pd.api.types.is_numeric_dtype(df[f]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feature '{f}' is not numerical (dtype: {df[f].dtype}). K-Means requires numerical features."
                )

        # 2. Extract and handle missing values
        clean_subset = df[req.features].dropna()
        n_samples = len(clean_subset)

        if n_samples < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset is not suitable for clustering because it has only {n_samples} non-null rows (minimum 10 required)."
            )

        # Check for constant columns
        constant_cols = [f for f in req.features if clean_subset[f].nunique() <= 1]
        if constant_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset is not suitable because column(s) {', '.join(constant_cols)} have constant values (zero variance)."
            )

        # Validate k vs samples
        if req.n_clusters >= n_samples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cluster count ({req.n_clusters}) cannot exceed or equal available rows ({n_samples})."
            )

        # 3. Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(clean_subset.values)

        # 4. Train KMeans
        kmeans = KMeans(n_clusters=req.n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # 5. Silhouette score
        sil_score = None
        if 2 <= req.n_clusters < n_samples:
            try:
                sil_score = round(float(silhouette_score(X_scaled, labels)), 4)
            except Exception as e:
                logger.warning("Could not calculate silhouette score: %s", e)

        # 6. Cluster counts and centers
        counts_series = pd.Series(labels).value_counts().sort_index()
        cluster_counts = {f"Cluster {int(k)}": int(v) for k, v in counts_series.items()}

        # Unscale centers for human interpretation
        unscaled_centers = scaler.inverse_transform(kmeans.cluster_centers_)
        cluster_centers = []
        for i, center in enumerate(unscaled_centers):
            center_dict = {f: round(float(val), 2) for f, val in zip(req.features, center)}
            center_dict["cluster"] = i
            cluster_centers.append(center_dict)

        # 7. Visualization
        plot_df = clean_subset.copy()
        plot_df["Cluster"] = [f"Cluster {l}" for l in labels]

        fig = None
        if len(req.features) == 2:
            fig = px.scatter(
                plot_df, x=req.features[0], y=req.features[1],
                color="Cluster",
                title=f"K-Means Clustering ({req.n_clusters} Clusters)",
                template="plotly_white"
            )
        else:
            # Use PCA 2D for multi-dimensional visualization
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X_scaled)
            plot_df["PCA 1"] = coords[:, 0]
            plot_df["PCA 2"] = coords[:, 1]
            var_explained = round(float(sum(pca.explained_variance_ratio_)) * 100, 1)
            fig = px.scatter(
                plot_df, x="PCA 1", y="PCA 2",
                color="Cluster",
                title=f"K-Means Clustering PCA Projection ({var_explained}% Variance Explained)",
                template="plotly_white"
            )

        fig_json = fig.to_json() if fig else None

        # Sample rows with cluster labels
        sample_df = df.loc[clean_subset.index].copy()
        sample_df["cluster"] = labels
        sample_rows = sample_df.head(10).replace({float("nan"): None}).to_dict(orient="records")

        explanation = (
            f"Trained K-Means with {req.n_clusters} clusters across {n_samples} records using features: "
            f"{', '.join(req.features)}. Silhouette score is {sil_score if sil_score is not None else 'N/A'}. "
            "Note: Cluster labels are machine-generated mathematical groupings based on feature similarity "
            "and do not represent predefined or subjective customer categories."
        )

        # Record in history
        history = AnalysisHistory(
            dataset_id=dataset.id,
            analysis_type="clustering",
            parameters=json.dumps({"features": req.features, "n_clusters": req.n_clusters}),
            result_summary=json.dumps({"cluster_counts": cluster_counts, "silhouette_score": sil_score})
        )
        db.add(history)
        db.commit()

        return ClusteringResponse(
            n_clusters=req.n_clusters,
            features=req.features,
            total_records=n_samples,
            cluster_counts=cluster_counts,
            cluster_centers=cluster_centers,
            silhouette_score=sil_score,
            explanation=explanation,
            figure_json=fig_json,
            sample_rows=sample_rows
        )
