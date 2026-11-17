import io
import pytest


def test_upload_dataset(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        response = client.post("/api/datasets/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["row_count"] > 0
    assert data["column_count"] > 0


def test_upload_empty_dataset(client):
    empty_file = io.BytesIO(b"")
    files = {"file": ("empty.csv", empty_file, "text/csv")}
    response = client.post("/api/datasets/upload", files=files)
    assert response.status_code == 400


def test_upload_unsupported_file(client):
    bad_file = io.BytesIO(b"some,data\n1,2")
    files = {"file": ("bad_script.sh", bad_file, "text/plain")}
    response = client.post("/api/datasets/upload", files=files)
    assert response.status_code == 400


def test_list_and_get_dataset(client, sample_csv_path):
    # Upload one
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    # List
    list_res = client.get("/api/datasets")
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert any(d["id"] == dataset_id for d in datasets)

    # Get by ID
    get_res = client.get(f"/api/datasets/{dataset_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == dataset_id


def test_preview_and_schema(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    # Preview
    prev_res = client.get(f"/api/datasets/{dataset_id}/preview")
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert len(prev_data["head"]) > 0
    assert "columns" in prev_data

    # Schema
    schema_res = client.get(f"/api/datasets/{dataset_id}/schema")
    assert schema_res.status_code == 200
    schema_data = schema_res.json()
    assert len(schema_data["columns"]) == prev_data["column_count"]


def test_delete_dataset(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    del_res = client.delete(f"/api/datasets/{dataset_id}")
    assert del_res.status_code == 200

    # Confirm 404
    get_res = client.get(f"/api/datasets/{dataset_id}")
    assert get_res.status_code == 404
