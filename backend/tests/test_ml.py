def test_kmeans_clustering(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    # Valid K-Means
    req = {
        "features": ["annual_income", "spending_score", "purchase_frequency"],
        "n_clusters": 3
    }
    res = client.post(f"/api/datasets/{dataset_id}/ml/clustering", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["n_clusters"] == 3
    assert len(data["cluster_counts"]) == 3
    assert data["silhouette_score"] is not None
    assert "figure_json" in data
    assert len(data["sample_rows"]) > 0

    # Validation: Less than 2 features
    bad_req = {"features": ["annual_income"], "n_clusters": 3}
    bad_res = client.post(f"/api/datasets/{dataset_id}/ml/clustering", json=bad_req)
    assert bad_res.status_code == 422 or bad_res.status_code == 400


def test_isolation_forest_anomaly(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    req = {
        "features": ["annual_income", "spending_score"],
        "contamination": 0.05
    }
    res = client.post(f"/api/datasets/{dataset_id}/ml/anomaly", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["anomaly_count"] > 0
    assert data["normal_count"] > 0
    assert data["anomaly_percentage"] > 0
    assert len(data["sample_anomalies"]) > 0


def test_linear_regression(client, sample_employee_csv_path):
    with open(sample_employee_csv_path, "rb") as f:
        files = {"file": ("employee_data.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    # Valid regression
    req = {
        "target_column": "salary",
        "feature_columns": ["experience", "age", "performance_score"],
        "test_size": 0.2
    }
    res = client.post(f"/api/datasets/{dataset_id}/ml/prediction", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["r2"] > 0.5  # Salary has strong correlation with experience in sample data
    assert data["mae"] > 0
    assert data["rmse"] > 0
    assert len(data["sample_predictions"]) > 0
    assert "figure_json" in data

    # Target leakage validation
    leakage_req = {
        "target_column": "salary",
        "feature_columns": ["salary", "experience"],
        "test_size": 0.2
    }
    leak_res = client.post(f"/api/datasets/{dataset_id}/ml/prediction", json=leakage_req)
    assert leak_res.status_code == 400
