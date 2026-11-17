import logging
from typing import Dict, Any, List, Optional, Tuple
import requests

from frontend.config import BACKEND_API_URL

logger = logging.getLogger("insightiq.api_client")
DEFAULT_TIMEOUT = 30


class APIClient:
    def __init__(self, base_url: str = BACKEND_API_URL):
        self.base_url = base_url.rstrip("/")

    def _handle_response(self, response: requests.Response) -> Tuple[Optional[Any], Optional[str]]:
        try:
            if response.status_code in [200, 201]:
                return response.json(), None
            try:
                err_data = response.json()
                detail = err_data.get("detail", response.text)
                if isinstance(detail, list):
                    detail = "; ".join(str(d) for d in detail)
                return None, f"Error ({response.status_code}): {detail}"
            except Exception:
                return None, f"Error ({response.status_code}): {response.text}"
        except Exception as exc:
            return None, f"Failed to parse response: {str(exc)}"

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=5)
            if res.status_code == 200:
                data = res.json()
                return True, data
            return False, {"message": f"Backend returned status {res.status_code}"}
        except requests.exceptions.ConnectionError:
            return False, {
                "message": f"Cannot connect to backend at {self.base_url}. Ensure the FastAPI server is running."
            }
        except Exception as exc:
            return False, {"message": str(exc)}

    def upload_dataset(self, file_bytes: bytes, filename: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            files = {"file": (filename, file_bytes, "application/octet-stream")}
            res = requests.post(f"{self.base_url}/api/datasets/upload", files=files, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except requests.exceptions.ConnectionError:
            return None, "Backend server is unreachable. Check your network or backend status."
        except Exception as exc:
            return None, str(exc)

    def list_datasets(self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        try:
            res = requests.get(f"{self.base_url}/api/datasets", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except requests.exceptions.ConnectionError:
            return None, "Backend server is unreachable."
        except Exception as exc:
            return None, str(exc)

    def get_dataset(self, dataset_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.get(f"{self.base_url}/api/datasets/{dataset_id}", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def delete_dataset(self, dataset_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.delete(f"{self.base_url}/api/datasets/{dataset_id}", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def get_preview(self, dataset_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.get(f"{self.base_url}/api/datasets/{dataset_id}/preview", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def get_schema(self, dataset_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.get(f"{self.base_url}/api/datasets/{dataset_id}/schema", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def get_statistics(self, dataset_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.get(f"{self.base_url}/api/datasets/{dataset_id}/statistics", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def preview_clean(self, dataset_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.post(f"{self.base_url}/api/datasets/{dataset_id}/clean/preview", json=payload, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def execute_clean(self, dataset_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.post(f"{self.base_url}/api/datasets/{dataset_id}/clean", json=payload, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def generate_visualization(self, dataset_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.post(f"{self.base_url}/api/datasets/{dataset_id}/visualization", json=payload, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def run_clustering(self, dataset_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.post(f"{self.base_url}/api/datasets/{dataset_id}/ml/clustering", json=payload, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def run_anomaly_detection(self, dataset_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.post(f"{self.base_url}/api/datasets/{dataset_id}/ml/anomaly", json=payload, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def run_prediction(self, dataset_id: int, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.post(f"{self.base_url}/api/datasets/{dataset_id}/ml/prediction", json=payload, timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def get_report(self, dataset_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            res = requests.get(f"{self.base_url}/api/datasets/{dataset_id}/report", timeout=DEFAULT_TIMEOUT)
            return self._handle_response(res)
        except Exception as exc:
            return None, str(exc)

    def download_dataset_bytes(self, dataset_id: int, format_type: str = "csv") -> Tuple[Optional[bytes], Optional[str]]:
        try:
            res = requests.get(
                f"{self.base_url}/api/datasets/{dataset_id}/download",
                params={"format": format_type},
                timeout=DEFAULT_TIMEOUT
            )
            if res.status_code == 200:
                return res.content, None
            return None, f"Failed to download ({res.status_code}): {res.text}"
        except Exception as exc:
            return None, str(exc)


api_client = APIClient()
