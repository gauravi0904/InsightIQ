import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.components.metric_cards import render_metric_card
from frontend.components.charts import render_plotly_json
from frontend.components.tables import render_preview_table


def render_ml_studio_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Machine Learning Studio
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Train, evaluate, and interpret production Scikit-learn models. All models execute on the backend with strict data validation.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    dataset_id = st.session_state.get("selected_dataset_id")
    if not dataset_id:
        st.warning("No dataset selected. Please select or upload a dataset first.")
        return

    # Fetch preview and schema to get numerical features
    preview, err = api_client.get_preview(dataset_id)
    if err:
        st.error(f"Failed to load dataset: {err}")
        return

    dtypes = preview["dtypes"]
    num_cols = [c for c, dt in dtypes.items() if "int" in dt or "float" in dt]

    if not num_cols:
        st.error("No numerical columns found in the active dataset. Machine learning algorithms require numerical features.")
        return

    ml_tab1, ml_tab2, ml_tab3 = st.tabs([
        "👥 Customer Segmentation (K-Means)",
        "⚠️ Anomaly Detection (Isolation Forest)",
        "🎯 Continuous Prediction (Linear Regression)"
    ])

    # ---------------- 13A. K-MEANS CLUSTERING ----------------
    with ml_tab1:
        st.markdown("### K-Means Clustering")
        st.info(
            "ℹ️ **Model Notice:** Cluster labels are machine-generated mathematical groupings based on feature similarity "
            "and do not represent predefined or subjective customer categories."
        )

        c1, c2 = st.columns([2, 1])
        with c1:
            default_feats = num_cols[:3] if len(num_cols) >= 3 else num_cols
            selected_features = st.multiselect(
                "Select Numerical Features (minimum 2):",
                num_cols,
                default=default_feats,
                key="kmeans_features"
            )
        with c2:
            n_clusters = st.slider("Number of Clusters (K):", min_value=2, max_value=min(10, max(2, preview["row_count"] - 1)), value=3)

        if st.button("🚀 Train K-Means Model", type="primary", key="btn_train_kmeans"):
            if len(selected_features) < 2:
                st.error("Please select at least 2 numerical features for clustering.")
            else:
                payload = {
                    "features": selected_features,
                    "n_clusters": n_clusters
                }
                with st.spinner("Standardizing features & training K-Means..."):
                    res, k_err = api_client.run_clustering(dataset_id, payload)
                    if k_err:
                        st.error(k_err)
                    else:
                        st.success("K-Means training completed successfully!")
                        st.markdown(f"**Explanation:** {res['explanation']}")

                        # Metrics
                        k_col1, k_col2, k_col3 = st.columns(3)
                        with k_col1:
                            render_metric_card("Clusters Formed", str(res["n_clusters"]))
                        with k_col2:
                            render_metric_card("Total Samples", f"{res['total_records']:,}")
                        with k_col3:
                            sil = res.get("silhouette_score")
                            render_metric_card("Silhouette Score", f"{sil:.3f}" if sil is not None else "N/A")

                        # Cluster Distribution Table
                        st.markdown("#### Cluster Sizes")
                        dist_df = pd.DataFrame([{"Cluster": k, "Count": v, "Percentage": f"{v/res['total_records']*100:.1f}%"} for k, v in res["cluster_counts"].items()])
                        st.dataframe(dist_df, use_container_width=True, hide_index=True)

                        # Visualization
                        if res.get("figure_json"):
                            st.markdown("#### Cluster Projection Chart")
                            render_plotly_json(res["figure_json"])

                        # Sample Clustered Rows
                        st.markdown("#### Sample Records with Assigned Clusters")
                        render_preview_table(res.get("sample_rows", []))

    # ---------------- 13B. ANOMALY DETECTION ----------------
    with ml_tab2:
        st.markdown("### Isolation Forest Anomaly Detection")
        st.info(
            "ℹ️ **Model Notice:** An anomaly is an unusual observation based on feature isolation depth. "
            "It is not automatically an error, fraud, or defect without domain-specific confirmation."
        )

        a1, a2 = st.columns([2, 1])
        with a1:
            iso_features = st.multiselect(
                "Select Features to Evaluate:",
                num_cols,
                default=num_cols[:2] if len(num_cols) >= 2 else num_cols,
                key="iso_features"
            )
        with a2:
            contamination = st.slider(
                "Expected Outlier Ratio (Contamination):",
                min_value=0.01,
                max_value=0.25,
                value=0.05,
                step=0.01,
                help="The proportion of outliers in the data set."
            )

        if st.button("🔍 Run Anomaly Detection", type="primary", key="btn_run_anomaly"):
            if not iso_features:
                st.error("Please select at least one feature for anomaly detection.")
            else:
                payload = {
                    "features": iso_features,
                    "contamination": contamination
                }
                with st.spinner("Fitting Isolation Forest ensemble..."):
                    res, a_err = api_client.run_anomaly_detection(dataset_id, payload)
                    if a_err:
                        st.error(a_err)
                    else:
                        st.success("Anomaly detection completed!")
                        st.markdown(f"**Findings:** {res['explanation']}")

                        m1, m2, m3 = st.columns(3)
                        with m1:
                            render_metric_card("Normal Records", f"{res['normal_count']:,}")
                        with m2:
                            render_metric_card("Anomalies Found", f"{res['anomaly_count']:,}", delta=f"{res['anomaly_percentage']}% of dataset")
                        with m3:
                            render_metric_card("Contamination Rate", f"{res['contamination']*100:.1f}%")

                        if res.get("figure_json"):
                            st.markdown("#### Anomaly Scatter Distribution")
                            render_plotly_json(res["figure_json"])

                        st.markdown("#### Top Detected Anomalous Records")
                        render_preview_table(res.get("sample_anomalies", []))

    # ---------------- 13C. LINEAR REGRESSION PREDICTION ----------------
    with ml_tab3:
        st.markdown("### Linear Regression Continuous Prediction")
        st.caption("Train a supervised multivariate regression model with train/test validation split.")

        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            target_col = st.selectbox("Target Column (Y to predict):", num_cols, key="reg_target")
        with p2:
            available_features = [c for c in num_cols if c != target_col]
            pred_features = st.multiselect(
                "Input Features (X):",
                available_features,
                default=available_features[:3] if available_features else [],
                key="reg_features"
            )
        with p3:
            test_split = st.slider("Test Split Ratio:", min_value=0.1, max_value=0.4, value=0.2, step=0.05)

        if st.button("⚡ Train & Evaluate Model", type="primary", key="btn_train_regression"):
            if not pred_features:
                st.error("Please select at least one input feature.")
            elif target_col in pred_features:
                st.error("Target leakage error: target cannot be included in input features.")
            else:
                payload = {
                    "target_column": target_col,
                    "feature_columns": pred_features,
                    "test_size": test_split
                }
                with st.spinner("Splitting data & training Linear Regression..."):
                    res, p_err = api_client.run_prediction(dataset_id, payload)
                    if p_err:
                        st.error(p_err)
                    else:
                        st.success("Regression model trained and evaluated!")
                        st.markdown(f"**Model Evaluation:** {res['explanation']}")

                        # Metrics
                        rm1, rm2, rm3 = st.columns(3)
                        with rm1:
                            render_metric_card("R² Score (Variance Explained)", f"{res['r2']:.3f}", "Higher is better (Max 1.0)")
                        with rm2:
                            render_metric_card("Mean Absolute Error (MAE)", f"{res['mae']:,.2f}", f"Avg error in {target_col}")
                        with rm3:
                            render_metric_card("Root Mean Squared Error", f"{res['rmse']:,.2f}", "Penalty for larger errors")

                        # Coefficients Table
                        st.markdown("#### Learned Feature Weights (Coefficients)")
                        coef_rows = [{"Feature": f, "Coefficient": c} for f, c in res["coefficients"].items()]
                        coef_rows.append({"Feature": "Intercept (Constant)", "Coefficient": res["intercept"]})
                        st.dataframe(pd.DataFrame(coef_rows), use_container_width=True, hide_index=True)

                        # Actual vs Predicted Plot
                        if res.get("figure_json"):
                            st.markdown("#### Actual vs Predicted Diagnostics")
                            render_plotly_json(res["figure_json"])

                        # Sample Predictions
                        st.markdown("#### Test Set Sample Predictions")
                        render_preview_table(res.get("sample_predictions", []))
