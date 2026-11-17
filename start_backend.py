import sys
import uvicorn
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings


def main():
    print(f"==================================================")
    print(f" Starting InsightIQ FastAPI Backend")
    print(f" Host: {settings.BACKEND_HOST}")
    print(f" Port: {settings.BACKEND_PORT}")
    print(f" Swagger UI: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/docs")
    print(f"==================================================")

    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
