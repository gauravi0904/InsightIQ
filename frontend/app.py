import streamlit as st
from frontend.config import APP_TITLE, APP_TAGLINE, APP_ICON, PAGES
from frontend.components.sidebar import render_sidebar
from frontend.pages.dashboard import render_dashboard_page
from frontend.pages.upload import render_upload_page
from frontend.pages.explorer import render_explorer_page
from frontend.pages.cleaning import render_cleaning_page
from frontend.pages.analytics import render_analytics_page
from frontend.pages.ml_studio import render_ml_studio_page
from frontend.pages.reports import render_reports_page
from frontend.pages.datasets import render_datasets_page

# Set Page Config
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_TAGLINE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom SaaS Styling
st.markdown(
    """
    <style>
        /* General styling */
        .main {
            background-color: #f8fafc;
        }
        h1, h2, h3, h4 {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            letter-spacing: -0.02em;
        }
        /* Metric container styling */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #0f172a !important;
        }
        /* Buttons */
        .stButton>button {
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            font-weight: 600;
            color: #475569;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            color: #2563eb !important;
            border-bottom: 2px solid #2563eb !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


def main():
    # Initialize Session State
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = PAGES["DASHBOARD"]
    if "selected_dataset_id" not in st.session_state:
        st.session_state["selected_dataset_id"] = None

    # Render Sidebar
    selected_page = render_sidebar()

    # Route Page
    if selected_page == PAGES["DASHBOARD"]:
        render_dashboard_page()
    elif selected_page == PAGES["UPLOAD"]:
        render_upload_page()
    elif selected_page == PAGES["EXPLORER"]:
        render_explorer_page()
    elif selected_page == PAGES["CLEANING"]:
        render_cleaning_page()
    elif selected_page == PAGES["ANALYTICS"]:
        render_analytics_page()
    elif selected_page == PAGES["ML_STUDIO"]:
        render_ml_studio_page()
    elif selected_page == PAGES["REPORTS"]:
        render_reports_page()
    elif selected_page == PAGES["DATASETS"]:
        render_datasets_page()
    else:
        render_dashboard_page()


if __name__ == "__main__":
    main()
