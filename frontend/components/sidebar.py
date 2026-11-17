import streamlit as st
from frontend.config import APP_TITLE, APP_TAGLINE, APP_ICON, PAGES
from frontend.api_client import api_client


def render_sidebar() -> str:
    with st.sidebar:
        # Brand Header
        st.markdown(
            f"""
            <div style="padding: 10px 0; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0;">
                <h1 style="margin: 0; font-size: 1.6rem; color: #1e293b; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #2563eb;">{APP_ICON}</span> {APP_TITLE}
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #64748b; font-weight: 500;">
                    {APP_TAGLINE}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Backend Health Check
        is_healthy, health_info = api_client.check_health()
        if is_healthy:
            db_status = health_info.get("database", "unknown")
            dialect = health_info.get("database_info", {}).get("dialect", "DB")
            st.markdown(
                f"""
                <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 8px 12px; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span style="font-size: 0.82rem; color: #065f46; font-weight: 600;">
                            <span style="color: #10b981; font-size: 1rem; margin-right: 4px;">●</span> Backend Connected
                        </span>
                        <span style="font-size: 0.72rem; background: #d1fae5; color: #047857; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-weight: 700;">
                            {dialect}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 8px 12px; margin-bottom: 16px;">
                    <span style="font-size: 0.82rem; color: #991b1b; font-weight: 600;">
                        <span style="color: #ef4444; font-size: 1rem; margin-right: 4px;">●</span> Backend Unavailable
                    </span>
                    <p style="margin: 4px 0 0 0; font-size: 0.75rem; color: #b91c1c;">
                        FastAPI is offline. Run <code>python run.py</code> to start both servers.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Navigation Options
        page_list = list(PAGES.values())
        current_page = st.session_state.get("current_page", PAGES["DASHBOARD"])
        try:
            curr_index = page_list.index(current_page)
        except ValueError:
            curr_index = 0

        selected_page = st.radio(
            "Navigation",
            options=page_list,
            index=curr_index,
            label_visibility="collapsed"
        )
        st.session_state["current_page"] = selected_page

        st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        # Active Dataset Selector
        st.markdown("<p style='font-size: 0.82rem; font-weight: 600; color: #475569; margin-bottom: 6px;'>ACTIVE DATASET</p>", unsafe_allow_html=True)
        datasets, err = api_client.list_datasets()
        if datasets and len(datasets) > 0:
            dataset_opts = {d["id"]: f"{d['dataset_name']} ({d['row_count']} rows)" for d in datasets}
            current_ds_id = st.session_state.get("selected_dataset_id")
            
            # Default to first if not set
            if current_ds_id not in dataset_opts:
                current_ds_id = datasets[0]["id"]
                st.session_state["selected_dataset_id"] = current_ds_id

            opts_keys = list(dataset_opts.keys())
            selected_id = st.selectbox(
                "Select active dataset",
                options=opts_keys,
                format_func=lambda x: dataset_opts[x],
                index=opts_keys.index(current_ds_id) if current_ds_id in opts_keys else 0,
                label_visibility="collapsed"
            )
            st.session_state["selected_dataset_id"] = selected_id
        else:
            st.info("No datasets uploaded yet.")
            st.session_state["selected_dataset_id"] = None

        # Footer
        st.markdown(
            """
            <div style="position: fixed; bottom: 12px; left: 16px; font-size: 0.72rem; color: #94a3b8;">
                InsightIQ Platform v1.0.0
            </div>
            """,
            unsafe_allow_html=True
        )

        return selected_page
