import os
import runpy
import json
import pytest
import requests

# The tests use requests-mock fixture provided by requests-mock plugin

def write_dummy_csv(tmp_path):
    exports = tmp_path / "exports"
    exports.mkdir()
    p = exports / "KPI_Mapping_Table.csv"
    p.write_text("col1,col2\n1,2\n")
    return exports


def test_figma_sync_success(requests_mock, tmp_path, monkeypatch, capsys):
    # Arrange: prepare exports and env
    exports_dir = write_dummy_csv(tmp_path)
    monkeypatch.setenv("EXPORTS_PATH", str(exports_dir))
    monkeypatch.setenv("FIGMA_TOKEN", "dummy_token")
    monkeypatch.setenv("FIGMA_FILE_KEY", "dummy_key")

    # Mock Figma GET response
    api_url = "https://api.figma.com/v1/files/dummy_key"
    mock_file = {
        "document": {
            "id": "0:0",
            "name": "Document",
            "children": [{"id": "page123", "name": "KPI Table", "children": []}],
        }
    }
    requests_mock.get(api_url, json=mock_file, status_code=200)

    # Intercept PUT (update) requests
    update_url = f"{api_url}/nodes?ids=page123"
    
    def put_callback(request, context):
        assert request.headers.get("X-Figma-Token") == "dummy_token"
        context.status_code = 200
        return {"ok": True}

    requests_mock.put(update_url, json=put_callback)

    # Act: run the script (script reads env vars and uses requests)
    runpy.run_path(str(os.path.abspath(os.path.join(os.getcwd(), "scripts", "sync_kpi_table_to_figma.py"))), run_name="__main__")

    # Assert: success message printed
    captured = capsys.readouterr()
    assert "KPI table synced to Figma" in captured.out


def test_figma_sync_rate_limit(requests_mock, tmp_path, monkeypatch):
    exports_dir = write_dummy_csv(tmp_path)
    monkeypatch.setenv("EXPORTS_PATH", str(exports_dir))
    monkeypatch.setenv("FIGMA_TOKEN", "dummy_token")
    monkeypatch.setenv("FIGMA_FILE_KEY", "bad_key")

    api_url = "https://api.figma.com/v1/files/bad_key"
    requests_mock.get(api_url, status_code=429, text="Too Many Requests")

    # Running the script should raise due to HTTP error
    with pytest.raises(RuntimeError) as exc:
        runpy.run_path(str(os.path.abspath(os.path.join(os.getcwd(), "scripts", "sync_kpi_table_to_figma.py"))), run_name="__main__")
    assert "Figma API request failed" in str(exc.value)
