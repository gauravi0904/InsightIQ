import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.config import PAGES
from frontend.components.metric_cards import render_metric_card


def render_dashboard_page():
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 2.2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Analytics Dashboard
            </h1>
            <p style="color: #64748b; font-size: 1rem; margin: 0;">
                Overview of your data warehouse, processing pipeline, and machine learning models.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch datasets
    datasets, err = api_client.list_datasets()
    if err:
        st.error(f"Failed to connect to backend service: {err}")
        return

    datasets = datasets or []
    total_datasets = len(datasets)
    total_rows = sum(d.get("row_count", 0) for d in datasets)
    total_cols = sum(d.get("column_count", 0) for d in datasets)
    latest_dataset = datasets[0] if datasets else None

    # Metric Cards Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Datasets", str(total_datasets), "Registered in InsightIQ")
    with col2:
        render_metric_card("Total Rows", f"{total_rows:,}", "Observations processed")
    with col3:
        latest_name = latest_dataset["dataset_name"] if latest_dataset else "None"
        render_metric_card("Latest Upload", latest_name, latest_dataset["upload_date"][:10] if latest_dataset else "No data")
    with col4:
        cleaned_cnt = sum(1 for d in datasets if d.get("processing_status") == "cleaned")
        render_metric_card("Cleaned Datasets", str(cleaned_cnt), f"{total_datasets - cleaned_cnt} raw uploads")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Quick Action Buttons
    st.markdown("### Quick Actions")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1:
        if st.button("📤 Upload New Dataset", use_container_width=True):
            st.session_state["current_page"] = PAGES["UPLOAD"]
            st.rerun()
    with q_col2:
        if st.button("🔍 Explore Data", use_container_width=True):
            st.session_state["current_page"] = PAGES["EXPLORER"]
            st.rerun()
    with q_col3:
        if st.button("📊 Run Analytics", use_container_width=True):
            st.session_state["current_page"] = PAGES["ANALYTICS"]
            st.rerun()
    with q_col4:
        if st.button("🤖 ML Studio", use_container_width=True):
            st.session_state["current_page"] = PAGES["ML_STUDIO"]
            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Recent Datasets Table
    st.markdown("### Recent Datasets")
    if not datasets:
        st.info("No datasets have been uploaded yet. Click 'Upload New Dataset' or load a sample dataset to get started!")
    else:
        df_display = pd.DataFrame([
            {
                "ID": d["id"],
                "Dataset Name": d["dataset_name"],
                "Original File": d["original_filename"],
                "Format": d["file_type"].upper(),
                "Rows": f"{d['row_count']:,}",
                "Columns": d["column_count"],
                "Status": d["processing_status"].capitalize(),
                "Uploaded": d["upload_date"][:16].replace("T", " ")
            }
            for d in datasets
        ])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
