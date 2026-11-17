import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.config import PAGES


def render_datasets_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Dataset Management
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Browse, activate, audit, and safely delete datasets stored in your InsightIQ repository.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    datasets, err = api_client.list_datasets()
    if err:
        st.error(f"Failed to fetch datasets: {err}")
        return

    datasets = datasets or []
    if not datasets:
        st.info("No datasets found. Please upload a dataset first.")
        return

    st.markdown(f"Total Datasets: **{len(datasets)}**")

    current_active_id = st.session_state.get("selected_dataset_id")

    for d in datasets:
        is_active = (d["id"] == current_active_id)
        border_color = "#3b82f6" if is_active else "#e2e8f0"
        bg_color = "#f8fafc" if is_active else "#ffffff"

        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid {border_color}; background: {bg_color}; border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-weight: 700; font-size: 1.1rem; color: #0f172a;">
                                {d['dataset_name']}
                            </span>
                            {'<span style="margin-left: 8px; background: #dbeafe; color: #1e40af; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; font-weight: 700;">ACTIVE</span>' if is_active else ''}
                            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                                File: <code>{d['original_filename']}</code> | Format: {d['file_type'].upper()} | Uploaded: {d['upload_date'][:16].replace('T', ' ')}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-weight: 600; font-size: 0.95rem; color: #1e293b;">
                                {d['row_count']:,} rows × {d['column_count']} cols
                            </span>
                            <div style="font-size: 0.75rem; color: #059669; font-weight: 600; text-transform: uppercase;">
                                {d['processing_status']}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Action buttons row
            b1, b2, b3, b4, b5 = st.columns([1, 1, 1, 1, 1])
            with b1:
                if not is_active:
                    if st.button("⭐ Set Active", key=f"act_{d['id']}", use_container_width=True):
                        st.session_state["selected_dataset_id"] = d["id"]
                        st.rerun()
                else:
                    st.button("Active", key=f"cur_{d['id']}", disabled=True, use_container_width=True)

            with b2:
                if st.button("🔍 Explore", key=f"exp_{d['id']}", use_container_width=True):
                    st.session_state["selected_dataset_id"] = d["id"]
                    st.session_state["current_page"] = PAGES["EXPLORER"]
                    st.rerun()

            with b3:
                if st.button("📊 Analytics", key=f"ana_{d['id']}", use_container_width=True):
                    st.session_state["selected_dataset_id"] = d["id"]
                    st.session_state["current_page"] = PAGES["ANALYTICS"]
                    st.rerun()

            with b4:
                if st.button("🤖 ML Studio", key=f"mls_{d['id']}", use_container_width=True):
                    st.session_state["selected_dataset_id"] = d["id"]
                    st.session_state["current_page"] = PAGES["ML_STUDIO"]
                    st.rerun()

            with b5:
                if st.button("🗑️ Delete", key=f"del_{d['id']}", type="secondary", use_container_width=True):
                    with st.spinner(f"Deleting '{d['dataset_name']}'..."):
                        del_res, d_err = api_client.delete_dataset(d["id"])
                        if d_err:
                            st.error(d_err)
                        else:
                            st.success(f"Deleted '{d['dataset_name']}'.")
                            if st.session_state.get("selected_dataset_id") == d["id"]:
                                st.session_state["selected_dataset_id"] = None
                            st.rerun()

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
