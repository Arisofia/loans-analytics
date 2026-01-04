import runpy
import requests
import pytest
from pathlib import Path

from src.config.paths import Paths

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "sync_kpi_table_to_figma.py"
CSV_NAME = "KPI_Mapping_Table.csv"


class DummyResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"Status {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture(autouse=True)
def ensure_exports_dir(tmp_path, monkeypatch):
    """Ensure the exports dir exists and is isolated for tests."""
    # Create a temp exports dir and point EXPORTS_PATH to it
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir(parents=True)
    monkeypatch.setenv("EXPORTS_PATH", str(exports_dir))
    # Ensure FIGMA secrets are set in env so the script doesn't try key vault
    monkeypatch.setenv("FIGMA_TOKEN", "dummy_token")
    monkeypatch.setenv("FIGMA_FILE_KEY", "dummy_file_key")
    yield


def write_csv(tmp_path, content="col1,col2\n1,2\n"):
    exports_dir = Paths.exports_dir(create=True)
    p = exports_dir / CSV_NAME
    p.write_text(content)
    return p


def test_sync_success(monkeypatch, capsys, tmp_path):
    write_csv(tmp_path)

    # Mock GET to return a file structure with the KPI Table page
    file_json = {"document": {"children": [{"name": "KPI Table", "id": "page123"}]}}
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResp(200, file_json))
    monkeypatch.setattr(requests, "put", lambda *args, **kwargs: DummyResp(200))

    # Run the script; it should print a success message
    runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

    captured = capsys.readouterr()
    assert "KPI table synced to Figma" in captured.out


def test_page_not_found(monkeypatch, tmp_path):
    write_csv(tmp_path)

    # GET returns a file without the KPI Table page
    file_json = {"document": {"children": [{"name": "Other Page", "id": "pageX"}]}}
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResp(200, file_json))

    with pytest.raises(ValueError) as exc:
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
    assert "Page 'KPI Table' not found" in str(exc.value)


def test_get_request_failure(monkeypatch, tmp_path):
    write_csv(tmp_path)

    def fail_get(*args, **kwargs):
        raise requests.exceptions.RequestException("network error")

    monkeypatch.setattr(requests, "get", fail_get)

    with pytest.raises(requests.exceptions.RequestException):
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")


def test_put_request_failure(monkeypatch, tmp_path):
    write_csv(tmp_path)

    file_json = {"document": {"children": [{"name": "KPI Table", "id": "page123"}]}}
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResp(200, file_json))

    def fail_put(*args, **kwargs):
        raise requests.exceptions.RequestException("put failed")

    monkeypatch.setattr(requests, "put", fail_put)

    with pytest.raises(requests.exceptions.RequestException):
        runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
