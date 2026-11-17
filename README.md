# InsightIQ — Smart Data Analytics & Machine Learning Platform

> *"Upload. Analyze. Predict. Visualize."*

InsightIQ is a modern, full-stack, decoupled platform designed for exploratory data analysis, data cleaning, automated statistical computation, interactive data visualization, and applied machine learning (Customer Segmentation, Anomaly Detection, and Numerical Regression).

---

## 📑 Table of Contents
1. [Overview & Features](#overview--features)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Quick Start (One-Command)](#quick-start-one-command)
7. [Step-by-Step Installation](#step-by-step-installation)
8. [Database Configuration & MySQL Setup](#database-configuration--mysql-setup)
9. [Running Services Independently](#running-services-independently)
10. [REST API Documentation & Swagger](#rest-api-documentation--swagger)
11. [Sample Datasets](#sample-datasets)
12. [Automated Testing](#automated-testing)
13. [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## 🌟 Overview & Features

InsightIQ bridges the gap between raw spreadsheet data and actionable data science workflows:

1. **Secure Dataset Ingestion**: Drag-and-drop CSV & Excel (`.xlsx`, `.xls`) file uploads up to 50MB with strict MIME/extension validation, payload sanitization, and filesystem protection.
2. **Metadata Repository & Dashboard**: Automatic calculation of observations, variables, missing cells, duplicates, and processing status.
3. **Data Explorer**: Paginated previews of first and last observations, column type inventory, non-null percentages, unique cardinality, and interactive sorting.
4. **Data Cleaning Studio**:
   - Duplicate removal
   - Numerical missing value imputation (`mean`, `median`)
   - Categorical missing value imputation (`mode`)
   - Complete case row dropping
   - Column renaming & dynamic data type conversion
   - Non-destructive processing: saves cleaned data without overwriting raw uploads
   - Real-time **Before vs After** comparison preview
5. **Descriptive Statistical Analytics**: Mean, median, standard deviation, quartiles (25%, 75%), min, max, missing count, unique count, and correlation matrix.
6. **Interactive Visualizations (Plotly)**: Dynamic chart builder with input validation for:
   - Histograms (with marginal distributions)
   - Scatter Plots (with grouping & trendlines)
   - Bar Charts (aggregated sums or category frequency distributions)
   - Line Charts
   - Box Plots
   - Pie Charts
7. **Machine Learning Studio**:
   - **Customer Segmentation (K-Means)**: Automated feature standardization (`StandardScaler`), cluster distribution analysis, silhouette scoring, and 2D PCA projection scatter plots.
   - **Anomaly Detection (Isolation Forest)**: Configurable contamination threshold, identification of multivariate outliers, and anomaly extraction.
   - **Continuous Prediction (Linear Regression)**: Train/test split validation, target leakage prevention, regression coefficients, sample predictions, and genuine performance metrics ($R^2$, MAE, RMSE).
8. **Reports & Multi-Sheet Exports**:
   - Comprehensive JSON audit reports
   - Single-click CSV export of cleaned datasets
   - Multi-sheet Excel workbook export (`.xlsx`) containing raw data, numerical statistics, and categorical metrics.
9. **Dataset Management**: Complete lifecycle management (explore, activate, audit, and cascade-delete metadata and physical files).

---

## 🏛️ Architecture

InsightIQ strictly enforces a clean separation of concerns. **Streamlit is strictly the presentation layer** and **FastAPI is strictly the business logic and analytics engine**.

```
                    +-----------------------------+
                    |        USER BROWSER         |
                    +-----------------------------+
                                   |
                                   v
                    +-----------------------------+
                    |    STREAMLIT FRONTEND       |
                    |    (Port 8501, UI Only)     |
                    +-----------------------------+
                                   |
                                   | HTTP REST API
                                   | (Centralized in api_client.py)
                                   v
                    +-----------------------------+
                    |       FASTAPI BACKEND       |
                    |    (Port 8000, App Logic)   |
                    +-----------------------------+
                                   |
            +----------------------+----------------------+
            |                      |                      |
            v                      v                      v
  +------------------+   +-------------------+  +-------------------+
  |     SERVICES     |   |     DATABASE      |  |   LOCAL STORAGE   |
  | Pandas / NumPy   |   | MySQL (Primary)   |  | data/uploads      |
  | Scikit-learn     |   | SQLite (Fallback) |  | data/processed    |
  | Plotly Engines   |   +-------------------+  | data/reports      |
  +------------------+                          +-------------------+
```

---

## 💻 Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0, PyMySQL
- **Data Processing**: Pandas, NumPy, OpenPyXL
- **Machine Learning**: Scikit-learn
- **Visualization**: Plotly
- **Frontend**: Streamlit
- **Database**: MySQL 8.0 (with automated local SQLite fallback when MySQL is offline)
- **Testing**: Pytest, FastAPI TestClient (HTTPX)

---

## 📁 Project Structure

```text
InsightIQ/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entrypoint & lifecycle
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py      # Master API router
│   │   │       ├── datasets.py      # Upload, list, preview, schema routes
│   │   │       ├── analytics.py     # Descriptive statistics & Plotly routes
│   │   │       ├── cleaning.py      # Imputation, transformation & preview routes
│   │   │       ├── ml.py            # K-Means, Isolation Forest, Regression routes
│   │   │       └── reports.py       # JSON report and file export routes
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Environment configuration & path resolver
│   │   │   └── database.py          # SQLAlchemy session & resilient connection pool
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py           # Dataset ORM table
│   │   │   └── analysis.py          # Analysis history audit ORM table
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── dataset.py           # Pydantic models for datasets & schema
│   │   │   ├── analytics.py         # Pydantic models for stats & cleaning
│   │   │   └── ml.py                # Pydantic models for clustering, anomaly & ML
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── dataset_service.py   # File ingestion, metadata & disk IO
│   │       ├── cleaning_service.py  # Imputation, renaming, type casting
│   │       ├── analytics_service.py # Descriptive statistics & correlations
│   │       ├── visualization_service.py # Plotly dynamic chart generators
│   │       ├── clustering_service.py    # K-Means segmentation & PCA
│   │       ├── anomaly_service.py   # Isolation Forest outlier detection
│   │       ├── prediction_service.py# Linear Regression & metric evaluation
│   │       └── report_service.py    # Multi-sheet Excel & CSV exports
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py              # Test database fixtures & client setup
│   │   ├── test_health.py           # Health endpoint tests
│   │   ├── test_datasets.py         # Upload, list, schema, delete tests
│   │   ├── test_analytics.py        # Descriptive stats, charts, export tests
│   │   ├── test_cleaning.py         # Preview and execution cleaning tests
│   │   └── test_ml.py               # Clustering, anomaly & regression tests
│   └── requirements.txt
│
├── frontend/
│   ├── app.py                       # Streamlit entrypoint & router
│   ├── api_client.py                # Centralized REST client with error wrapping
│   ├── config.py                    # Frontend constants and endpoints
│   ├── components/
│   │   ├── __init__.py
│   │   ├── sidebar.py               # Branding, health indicator, dataset selector
│   │   ├── metric_cards.py          # SaaS styled KPI cards
│   │   ├── charts.py                # Plotly JSON figure renderer
│   │   └── tables.py                # Dataframe preview wrapper
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py             # KPI overview & quick action triggers
│       ├── upload.py                # File uploader & sample dataset loader
│       ├── explorer.py              # Schema, head/tail, and column filters
│       ├── cleaning.py              # Cleaning studio with before/after stats
│       ├── analytics.py             # Statistical tables & chart generator
│       ├── ml_studio.py             # K-Means, Isolation Forest, Regression tabs
│       ├── reports.py               # Executive report & Excel/CSV download
│       └── datasets.py              # Dataset inventory & deletion management
│
├── data/
│   ├── uploads/                     # Storage for raw uploaded files
│   ├── processed/                   # Storage for cleaned datasets
│   └── reports/                     # Storage for generated reports
│
├── sample_data/
│   ├── customers.csv                # Sample customer demographics & scores
│   ├── sales.csv                    # Sample e-commerce transactions
│   └── employee_data.csv            # Sample employee compensation & tenure
│
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore configuration
├── docker-compose.yml               # MySQL 8.0 Docker container definition
├── requirements.txt                 # Project-level dependencies
├── run.py                           # Single-command launcher (Backend + Frontend)
├── start_backend.py                 # Standalone backend launcher
└── start_frontend.py                # Standalone frontend launcher
```

---

## ⚙️ Prerequisites

- **Python 3.11+** installed (`python3 --version` should be >= 3.11)
- **Git** (optional, for version control)
- **Docker / Docker Compose** (optional, for running MySQL in a container)

---

## 🚀 Quick Start (One-Command)

### 1. Clone or Extract Project
Navigate to the project root directory:
```bash
cd InsightIQ
```

### 2. Set Up Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (Command Prompt / PowerShell):**
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment File
```bash
cp .env.example .env
```

### 4. Run Everything with ONE Command
```bash
python run.py
```
`run.py` automatically:
1. Validates the environment and directory structure.
2. Launches the FastAPI backend on `http://127.0.0.1:8000`.
3. Waits for the `/health` endpoint to pass.
4. Launches the Streamlit frontend on `http://127.0.0.1:8501`.
5. Automatically opens your browser and coordinates graceful shutdown on `Ctrl+C`.

---

## 🗄️ Database Configuration & MySQL Setup

InsightIQ connects to MySQL by default via SQLAlchemy using the credentials defined in `.env`.

### OPTION A: Docker Compose MySQL (Recommended)
If you have Docker installed, start the pre-configured MySQL 8 container with:
```bash
docker compose up -d
```
This runs MySQL 8 with:
- **Host**: `localhost:3306`
- **Database**: `insightiq`
- **User**: `root`
- **Password**: `password`

### OPTION B: Existing Local MySQL Service
Create the database in your local MySQL instance:
```sql
CREATE DATABASE insightiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Then update your `.env` file:
```env
DATABASE_URL=mysql+pymysql://<username>:<password>@localhost:3306/insightiq
```

### Automatic Tables Creation
You do **NOT** need to manually execute SQL scripts. When the backend initializes, SQLAlchemy automatically creates the `datasets` and `analysis_history` tables if they do not exist.

### Automatic SQLite Resilience Fallback
If MySQL is temporarily unreachable or not yet running, InsightIQ logs a clear diagnostic message and automatically falls back to local SQLite storage at `data/insightiq_local.sqlite3`. This guarantees that you can test and explore the application immediately without getting blocked by a database service failure.

---

## 🖥️ Running Services Independently

If you prefer separate terminals for backend and frontend:

### Terminal 1: Backend
```bash
source .venv/bin/activate
python start_backend.py
```
- API Server: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`

### Terminal 2: Frontend
```bash
source .venv/bin/activate
python start_frontend.py
```
- Web Application: `http://127.0.0.1:8501`

---

## 📖 REST API Documentation & Swagger

The FastAPI backend exposes fully typed REST endpoints documented with OpenAPI 3.0 at `http://127.0.0.1:8000/docs`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Application and database connection health check |
| `POST`| `/api/datasets/upload` | Upload & register CSV/Excel dataset |
| `GET` | `/api/datasets` | List all registered datasets |
| `GET` | `/api/datasets/{id}` | Retrieve dataset metadata |
| `DELETE`| `/api/datasets/{id}` | Delete dataset metadata and physical files |
| `GET` | `/api/datasets/{id}/preview` | Retrieve head, tail, duplicates, and missing counts |
| `GET` | `/api/datasets/{id}/schema` | Retrieve detailed column types and sample values |
| `GET` | `/api/datasets/{id}/statistics`| Descriptive statistical summary & correlation matrix |
| `POST`| `/api/datasets/{id}/clean/preview` | Preview transformation results before saving |
| `POST`| `/api/datasets/{id}/clean` | Execute non-destructive data cleaning |
| `POST`| `/api/datasets/{id}/visualization` | Generate interactive Plotly JSON chart |
| `POST`| `/api/datasets/{id}/ml/clustering` | Run K-Means segmentation & silhouette evaluation |
| `POST`| `/api/datasets/{id}/ml/anomaly` | Run Isolation Forest anomaly detection |
| `POST`| `/api/datasets/{id}/ml/prediction` | Train Linear Regression & compute $R^2$, MAE, RMSE |
| `GET` | `/api/datasets/{id}/report` | Generate structured executive report JSON |
| `GET` | `/api/datasets/{id}/download` | Export dataset as `.csv` or multi-sheet `.xlsx` |

---

## 🧪 Sample Datasets

Located in the `sample_data/` directory and loadable with one click directly in the UI under **Upload Dataset > Load Sample Datasets**:

1. **`customers.csv`** (150 rows): Contains `customer_id`, `age`, `annual_income`, `spending_score`, `purchase_frequency`, and `region`. Ideal for demonstrating **K-Means Clustering** and demographic segmentation.
2. **`sales.csv`** (200 rows): Contains `order_id`, `order_date`, `product`, `category`, `quantity`, `unit_price`, `sales`, and `region`. Ideal for **Bar Charts, Line Trends, and Pie Charts**.
3. **`employee_data.csv`** (120 rows): Contains `employee_id`, `age`, `department`, `salary`, `experience`, and `performance_score`. Ideal for **Linear Regression Prediction** (predicting `salary` from `experience` and `performance_score`) and **Isolation Forest Anomaly Detection**.

---

## 🔬 Automated Testing

The automated test suite runs through `pytest` and verifies health, dataset ingestion, preview generation, schema inspection, statistical computation, data cleaning transformations, ML workflows (Clustering, Anomaly Detection, Regression), and file deletion.

To run the automated tests:
```bash
pytest backend/tests -v
```

Expected output:
```text
backend/tests/test_analytics.py::test_compute_statistics PASSED
backend/tests/test_analytics.py::test_visualizations PASSED
backend/tests/test_analytics.py::test_reports_and_downloads PASSED
backend/tests/test_cleaning.py::test_cleaning_preview PASSED
backend/tests/test_cleaning.py::test_cleaning_execution PASSED
backend/tests/test_datasets.py::test_upload_dataset PASSED
backend/tests/test_datasets.py::test_upload_empty_dataset PASSED
backend/tests/test_datasets.py::test_upload_unsupported_file PASSED
backend/tests/test_datasets.py::test_list_and_get_dataset PASSED
backend/tests/test_datasets.py::test_preview_and_schema PASSED
backend/tests/test_datasets.py::test_delete_dataset PASSED
backend/tests/test_health.py::test_health_check PASSED
backend/tests/test_ml.py::test_kmeans_clustering PASSED
backend/tests/test_ml.py::test_isolation_forest_anomaly PASSED
backend/tests/test_ml.py::test_linear_regression PASSED
======================== 15 passed in 0.36s ========================
```

---

## 🔧 Troubleshooting & FAQs

### Q: Why does the sidebar show "SQLite" instead of "MySQL"?
A: If MySQL is not running locally or Docker is not active, InsightIQ's graceful connection resilience kicks in so you can immediately use the app with SQLite fallback. To switch to MySQL:
1. Start your MySQL server or run `docker compose up -d`.
2. Confirm credentials in `.env`.
3. Restart the backend (`python run.py`).

### Q: How do I resolve "Address already in use" errors?
A: If port 8000 or 8501 is occupied by an older process:
- On macOS/Linux: `lsof -ti :8000 | xargs kill -9` and `lsof -ti :8501 | xargs kill -9`
- Or change `BACKEND_PORT=8001` and `FRONTEND_PORT=8502` in your `.env` file.

### Q: Are original uploaded files modified during data cleaning?
A: **No.** Original uploads are strictly immutable. Cleaned datasets are saved to `data/processed/` and registered with status `cleaned`, preserving the raw uploaded file.

---

## 📄 License
InsightIQ is distributed under the MIT Open Source License.
