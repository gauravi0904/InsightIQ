import os

# Backend API URL
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", f"http://{BACKEND_HOST}:{BACKEND_PORT}")

# App Info
APP_TITLE = "InsightIQ"
APP_TAGLINE = "Upload. Analyze. Predict. Visualize."
APP_ICON = "⚡"

# Navigation Pages
PAGES = {
    "DASHBOARD": "Dashboard",
    "UPLOAD": "Upload Dataset",
    "EXPLORER": "Data Explorer",
    "CLEANING": "Data Cleaning",
    "ANALYTICS": "Statistical Analytics",
    "ML_STUDIO": "ML Studio",
    "REPORTS": "Reports & Export",
    "DATASETS": "Dataset Management",
}
