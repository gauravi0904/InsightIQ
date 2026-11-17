import os
from pathlib import Path
import streamlit as st
from frontend.api_client import api_client
from frontend.config import PAGES

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data"


def render_upload_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Upload Dataset
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Upload your CSV or Excel files. Files are validated, sanitized, and indexed securely.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["📁 Upload Your File", "🧪 Load Sample Datasets"])

    with tab1:
        st.markdown("#### Select File (.csv, .xlsx, .xls)")
        uploaded_file = st.file_uploader(
            "Choose a dataset file (Max: 50MB)",
            type=["csv", "xlsx", "xls"],
            help="Files are validated for non-empty content and tabular integrity."
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            size_mb = len(file_bytes) / (1024 * 1024)

            st.write(f"**Filename:** `{filename}` | **Size:** `{size_mb:.2f} MB`")

            if st.button("🚀 Process and Register Dataset", type="primary"):
                with st.spinner("Uploading and analyzing dataset schema..."):
                    result, err = api_client.upload_dataset(file_bytes, filename)
                    if err:
                        st.error(f"Upload failed: {err}")
                    else:
                        st.success(f"Successfully uploaded '{result['dataset_name']}'!")
                        st.session_state["selected_dataset_id"] = result["id"]
                        st.session_state["current_page"] = PAGES["EXPLORER"]
                        st.rerun()

    with tab2:
        st.markdown("#### Ready-to-Use Sample Datasets")
        st.write("Explore InsightIQ immediately using pre-configured benchmark datasets:")

        samples = [
            ("customers.csv", "Customer Demographics & Segmentation", "Ideal for K-Means clustering and demographic analytics."),
            ("sales.csv", "E-Commerce Multi-Category Sales", "Ideal for line/bar charts, revenue distributions, and category share."),
            ("employee_data.csv", "Enterprise Employee Compensation", "Ideal for Linear Regression prediction and anomaly detection.")
        ]

        for s_file, s_title, s_desc in samples:
            s_path = SAMPLE_DATA_DIR / s_file
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{s_title}** (`{s_file}`)")
                st.caption(s_desc)
            with c2:
                if s_path.exists():
                    if st.button(f"Load {s_file}", key=f"load_{s_file}", use_container_width=True):
                        with open(s_path, "rb") as f_in:
                            bytes_data = f_in.read()
                        with st.spinner(f"Loading {s_file}..."):
                            res, err = api_client.upload_dataset(bytes_data, s_file)
                            if err:
                                st.error(err)
                            else:
                                st.success(f"Loaded '{res['dataset_name']}'!")
                                st.session_state["selected_dataset_id"] = res["id"]
                                st.session_state["current_page"] = PAGES["EXPLORER"]
                                st.rerun()
                else:
                    st.caption("Not found on disk")
            st.divider()
