def test_cleaning_preview(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    req = {
        "remove_duplicates": True,
        "fill_numeric": "mean",
        "rename_columns": {"region": "customer_region"}
    }
    prev_res = client.post(f"/api/datasets/{dataset_id}/clean/preview", json=req)
    assert prev_res.status_code == 200
    data = prev_res.json()
    assert "before_rows" in data
    assert "after_rows" in data
    assert len(data["changes_summary"]) > 0


def test_cleaning_execution(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    req = {
        "remove_duplicates": True,
        "fill_numeric": "median",
        "save_as_new": True,
        "new_dataset_name": "customers_clean_v1"
    }
    exec_res = client.post(f"/api/datasets/{dataset_id}/clean", json=req)
    assert exec_res.status_code == 200
    res_data = exec_res.json()
    assert res_data["status"] == "success"
    new_id = res_data["dataset_id"]
    assert new_id != dataset_id

    # Verify new dataset is in list
    list_res = client.get("/api/datasets")
    assert any(d["id"] == new_id for d in list_res.json())
