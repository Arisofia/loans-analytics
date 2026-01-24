import json

from fastapi.testclient import TestClient

from apps.analytics.api import main as api_main



def test_get_latest_kpis(tmp_path):
    # Arrange: create a fake manifest under a temporary artifacts dir
    run_dir = tmp_path / "logs" / "runs" / "run123"
    run_dir.mkdir(parents=True)

    manifest = {
        "run_id": "run123",
        "generated_at": "2026-01-01T00:00:00Z",
        "metrics": {"aum": 100.0, "par90": 5.5, "aum_growth": -10.0},
        "quality_checks": {},
    }
    manifest_path = run_dir / "run123_manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    # Point the API to the temporary artifacts dir and exercise the endpoint
    api_main.ARTIFACTS_DIR = tmp_path / "logs" / "runs"
    client = TestClient(api_main.app)

    res = client.get("/api/kpis/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == "run123"
    assert "metrics" in data
    assert data["metrics"]["aum"] == 100.0
