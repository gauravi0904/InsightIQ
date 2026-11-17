import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings


def main():
    print(f"==================================================")
    print(f" Starting InsightIQ Streamlit Frontend")
    print(f" Host: {settings.FRONTEND_HOST}")
    print(f" Port: {settings.FRONTEND_PORT}")
    print(f" URL:  http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}")
    print(f"==================================================")

    app_path = PROJECT_ROOT / "frontend" / "app.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        settings.FRONTEND_HOST,
        "--server.port",
        str(settings.FRONTEND_PORT),
        "--browser.gatherUsageStats",
        "false"
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopping InsightIQ frontend.")


if __name__ == "__main__":
    main()
