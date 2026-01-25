import json
import re
import pytest
from pathlib import Path
from urllib.parse import urlparse, parse_qs


SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "sync_kpi_table_to_figma.py"


def load_fixture(name: str):
    p = Path(__file__).resolve().parent.parent / "fixtures" / "figma" / name
    return json.loads(p.read_text())


def test_figma_sync_with_requests_mock(requests_mock, tmp_path, monkeypatch, capsys):
    # Prepare exports and CSV
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    monkeypatch.setenv("EXPORTS_PATH", str(exports_dir))
    monkeypatch.setenv("FIGMA_TOKEN", "dummy_token")
    monkeypatch.setenv("FIGMA_FILE_KEY", "dummy_key")

    csv = exports_dir / "KPI_Mapping_Table.csv"
    csv.write_text("col1,col2\n1,2\n")

    # Load the fixture
    file_json = load_fixture("valid_file.json")

    api_url = "https://api.figma.com/v1/files/dummy_key"

    # Mock GET to Figma file
    requests_mock.get(api_url, json=file_json, status_code=200, headers={"content-type": "application/json"})

    # Intercept the PUT/update request and assert headers/payload
    # Use regex to match URL with query parameters robustly
    update_regex = re.compile(rf"^{re.escape(api_url)}/nodes\?ids=.*$")

    def put_callback(request, context):
        assert request.headers.get("X-Figma-Token") == "dummy_token"
        
        # Verify URL structure
        parsed = urlparse(request.url)
        assert parsed.path.endswith("/nodes")
        qs = parse_qs(parsed.query)
        assert "ids" in qs
        assert "page123" in qs["ids"] or "page123" in qs["ids"][0].split(",")

        payload = request.json()
        # Expect the payload to include our KPI content (simple check)
        assert "characters" in payload or "document" in payload
        context.status_code = 200
        return {"ok": True}

    requests_mock.put(update_regex, json=put_callback)

    # Run the script; should complete without raising
    import runpy

    runpy.run_path(str(SCRIPT), run_name="__main__")

    captured = capsys.readouterr()
    assert "KPI table synced to Figma" in captured.out


def test_figma_sync_handles_rate_limit(requests_mock, tmp_path, monkeypatch):
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    monkeypatch.setenv("EXPORTS_PATH", str(exports_dir))
    monkeypatch.setenv("FIGMA_TOKEN", "dummy_token")
    monkeypatch.setenv("FIGMA_FILE_KEY", "bad_key")

    csv = exports_dir / "KPI_Mapping_Table.csv"
    csv.write_text("col1,col2\n1,2\n")

    api_url = "https://api.figma.com/v1/files/bad_key"
    requests_mock.get(api_url, status_code=429)

    import runpy

    with pytest.raises(Exception):
        runpy.run_path(str(SCRIPT), run_name="__main__")
