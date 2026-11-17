def test_compute_statistics(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    stats_res = client.get(f"/api/datasets/{dataset_id}/statistics")
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert len(data["numerical_stats"]) > 0
    assert len(data["categorical_stats"]) > 0

    # Ensure mean, median, min, max exist for numerical
    num_col = data["numerical_stats"][0]
    assert num_col["mean"] is not None
    assert num_col["median"] is not None


def test_visualizations(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    # Valid Histogram
    hist_req = {"chart_type": "histogram", "x_column": "age"}
    res = client.post(f"/api/datasets/{dataset_id}/visualization", json=hist_req)
    assert res.status_code == 200
    assert "figure_json" in res.json()

    # Valid Scatter
    scatter_req = {"chart_type": "scatter", "x_column": "annual_income", "y_column": "spending_score"}
    res = client.post(f"/api/datasets/{dataset_id}/visualization", json=scatter_req)
    assert res.status_code == 200

    # Incompatible scatter (categorical on numeric)
    bad_scatter = {"chart_type": "scatter", "x_column": "region", "y_column": "annual_income"}
    bad_res = client.post(f"/api/datasets/{dataset_id}/visualization", json=bad_scatter)
    assert bad_res.status_code == 400


def test_reports_and_downloads(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        files = {"file": ("customers.csv", f, "text/csv")}
        up_res = client.post("/api/datasets/upload", files=files)
    dataset_id = up_res.json()["id"]

    # JSON report
    rep_res = client.get(f"/api/datasets/{dataset_id}/report")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "dataset" in rep_data
    assert "numerical_statistics" in rep_data

    # Download CSV
    csv_dl = client.get(f"/api/datasets/{dataset_id}/download?format=csv")
    assert csv_dl.status_code == 200
    assert "text/csv" in csv_dl.headers.get("content-type", "")

    # Download XLSX
    xlsx_dl = client.get(f"/api/datasets/{dataset_id}/download?format=xlsx")
    assert xlsx_dl.status_code == 200
