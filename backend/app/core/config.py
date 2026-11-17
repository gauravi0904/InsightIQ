import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("insightiq.config")

# Project root is 3 levels up from backend/app/core:
# backend/app/core/config.py -> core -> app -> backend -> PROJECT_ROOT
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Load .env file
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("Loaded configuration from %s", env_path)
else:
    example_path = PROJECT_ROOT / ".env.example"
    logger.warning(
        ".env file not found at %s. Using default configurations. "
        "To customize, copy %s to .env and adjust variables.",
        env_path, example_path
    )


class Settings:
    PROJECT_NAME: str = "InsightIQ"
    PROJECT_TAGLINE: str = "Upload. Analyze. Predict. Visualize."
    PROJECT_ROOT: Path = PROJECT_ROOT

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/insightiq"
    )
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "127.0.0.1")
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))

    UPLOAD_DIR: Path = PROJECT_ROOT / os.getenv("UPLOAD_DIR", "data/uploads")
    PROCESSED_DIR: Path = PROJECT_ROOT / os.getenv("PROCESSED_DIR", "data/processed")
    REPORT_DIR: Path = PROJECT_ROOT / os.getenv("REPORT_DIR", "data/reports")

    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls"}

    FALLBACK_SQLITE_IF_MYSQL_UNAVAILABLE: bool = os.getenv(
        "FALLBACK_SQLITE_IF_MYSQL_UNAVAILABLE", "true"
    ).lower() in ("1", "true", "yes")

    CORS_ORIGINS: list = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    def ensure_directories(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
