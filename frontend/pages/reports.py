import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.components.metric_cards import render_metric_card


def render_reports_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Analytics Reports & Data Export
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Generate structured business intelligence summaries, data audit logs, and export multi-sheet spreadsheets.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    dataset_id = st.session_state.get("selected_dataset_id")
    if not dataset_id:
        st.warning("No dataset selected. Please select or upload a dataset first.")
        return

    # Fetch report JSON
    report_data, err = api_client.get_report(dataset_id)
    if err:
        st.error(f"Failed to generate report: {err}")
        return

    ds_info = report_data["dataset"]
    quality = report_data["data_quality"]

    # Export Section
    st.markdown("### 📥 Download & Export")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        csv_bytes, c_err = api_client.download_dataset_bytes(dataset_id, format_type="csv")
        if csv_bytes:
            st.download_button(
                label="📄 Download Processed Dataset (CSV)",
                data=csv_bytes,
                file_name=f"{ds_info['name']}_export.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.button("Download CSV (Unavailable)", disabled=True, use_container_width=True)

    with d_col2:
        xlsx_bytes, x_err = api_client.download_dataset_bytes(dataset_id, format_type="xlsx")
        if xlsx_bytes:
            st.download_button(
                label="📊 Download Multi-Sheet Workbook (Excel .xlsx)",
                data=xlsx_bytes,
                file_name=f"{ds_info['name']}_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.button("Download Excel (Unavailable)", disabled=True, use_container_width=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Dataset Summary Card
    st.markdown("### 📋 Executive Dataset Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Dataset Name", ds_info["name"])
    with c2:
        render_metric_card("Observations", f"{ds_info['row_count']:,}")
    with c3:
        render_metric_card("Variables", str(ds_info["column_count"]))
    with c4:
        size_kb = ds_info["file_size_bytes"] / 1024
        render_metric_card("File Size", f"{size_kb:,.1f} KB", ds_info["file_type"].upper())

    # Data Quality Section
    st.markdown("### 🛡️ Data Quality Audit")
    q1, q2 = st.columns(2)
    with q1:
        st.metric("Total Missing Cells", f"{quality['total_missing_cells']:,}")
    with q2:
        st.metric("Duplicate Observations", f"{quality['duplicate_rows']:,}")

    # Analysis History Log
    st.markdown("### 📜 Analysis Audit Trail")
    history = report_data.get("analysis_history", [])
    if history:
        hist_rows = []
        for h in history:
            hist_rows.append({
                "ID": h["id"],
                "Operation Type": h["analysis_type"].upper(),
                "Parameters": str(h.get("parameters", {})),
                "Summary": str(h.get("result_summary", {})),
                "Timestamp": h["created_at"][:19].replace("T", " ") if h.get("created_at") else "N/A"
            })
        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No prior ML runs or cleaning operations recorded for this dataset.")
