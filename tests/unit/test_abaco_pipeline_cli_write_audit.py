from __future__ import annotations

import json
from unittest.mock import Mock, patch

from src.abaco_pipeline.main import main


def test_write_audit_dry_run_prints_enriched_payload(tmp_path, capsys, monkeypatch):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "run": {
                    "run_id": "00000000-0000-0000-0000-000000000000",
                    "status": "success",
                    "started_at": "2025-12-31T00:00:00Z",
                },
                "raw_artifacts": [],
                "kpi_values": [
                    {
                        "run_id": "00000000-0000-0000-0000-000000000000",
                        "as_of": "2025-12-31T00:00:00Z",
                        "kpi_name": "par_90",
                        "value_numeric": 0.01,
                        "precision": 4,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rc = main(
        [
            "--config",
            "config/pipeline.yml",
            "write-audit",
            "--kpis-config",
            "config/kpis.yml",
            "--payload",
            str(payload_path),
            "--dry-run",
        ]
    )
    assert rc == 0

    out = capsys.readouterr().out
    assert "config_version" in out
    assert "git_sha" in out
    assert "kpi_def_version" in out


@patch("src.abaco_pipeline.main.subprocess.check_output")
@patch("src.abaco_pipeline.output.supabase_writer.requests.post")
def test_write_audit_writes_to_supabase(mock_post: Mock, mock_git: Mock, tmp_path, monkeypatch):
    mock_git.return_value = b"abc123\n"
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_post.return_value = mock_resp

    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "run": {
                    "run_id": "00000000-0000-0000-0000-000000000000",
                    "status": "success",
                    "started_at": "2025-12-31T00:00:00Z",
                },
                "raw_artifacts": [],
                "kpi_values": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE", "svc")

    rc = main(
        [
            "--config",
            "config/pipeline.yml",
            "write-audit",
            "--kpis-config",
            "config/kpis.yml",
            "--payload",
            str(payload_path),
        ]
    )
    assert rc == 0
    assert mock_post.call_count >= 1
