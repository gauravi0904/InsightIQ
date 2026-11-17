import sys
import time
import subprocess
import signal
from pathlib import Path
import urllib.request
import json

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings


def wait_for_backend(url: str, timeout: int = 15) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(f"{url}/health")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    print("""
============================================================
              InsightIQ - Platform Launcher
        "Upload. Analyze. Predict. Visualize."
============================================================
    """)

    backend_url = f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}"
    frontend_url = f"http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}"

    print(f"[*] Starting Backend at {backend_url}...")
    backend_script = PROJECT_ROOT / "start_backend.py"
    backend_proc = subprocess.Popen(
        [sys.executable, str(backend_script)],
        cwd=str(PROJECT_ROOT)
    )

    print("[*] Waiting for Backend to be ready...")
    ready = wait_for_backend(backend_url, timeout=15)
    if ready:
        print(f"[+] Backend is ready! Health check passed at {backend_url}/health")
        print(f"[+] API Documentation available at {backend_url}/docs")
    else:
        print(f"[!] Warning: Backend health check timed out. Proceeding anyway...")

    print(f"[*] Starting Frontend at {frontend_url}...")
    frontend_script = PROJECT_ROOT / "start_frontend.py"

    try:
        frontend_proc = subprocess.Popen(
            [sys.executable, str(frontend_script)],
            cwd=str(PROJECT_ROOT)
        )
        print("\n============================================================")
        print(f"  InsightIQ is running!")
        print(f"  • Frontend: {frontend_url}")
        print(f"  • Backend:  {backend_url}")
        print(f"  • Swagger:  {backend_url}/docs")
        print("  Press Ctrl+C to stop all services.")
        print("============================================================\n")

        # Wait on frontend process
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n[!] Received stop signal. Shutting down InsightIQ services...")
    finally:
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()

        try:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=3)
        except Exception:
            pass

        print("[+] All services terminated cleanly. Goodbye!")


if __name__ == "__main__":
    main()
