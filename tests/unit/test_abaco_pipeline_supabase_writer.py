from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.abaco_pipeline.output.supabase_writer import SupabaseAuth, SupabaseWriter


@patch("src.abaco_pipeline.output.supabase_writer.requests.post")
def test_upsert_pipeline_run_posts_expected_url_headers_and_body(mock_post: Mock):
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_post.return_value = mock_resp

    writer = SupabaseWriter(
        SupabaseAuth(url="https://example.supabase.co/", service_role_key="svc")
    )
    run = {
        "run_id": "00000000-0000-0000-0000-000000000000",
        "started_at": datetime(2025, 12, 31, 0, 0, tzinfo=timezone.utc),
        "config_version": "2025-12-31",
        "git_sha": "abc123",
        "status": "running",
    }

    writer.upsert_pipeline_run(run)

    assert mock_post.call_count == 1
    url = mock_post.call_args.args[0]
    assert url.startswith("https://example.supabase.co/rest/v1/analytics.pipeline_runs")
    assert "on_conflict=run_id" in url

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["apikey"] == "svc"
    assert headers["Authorization"] == "Bearer svc"
    assert "resolution=merge-duplicates" in headers.get("Prefer", "")

    body = json.loads(mock_post.call_args.kwargs["data"])
    assert isinstance(body, list) and body[0]["run_id"] == run["run_id"]
    assert body[0]["started_at"].startswith("2025-12-31T00:00:00")


@patch("src.abaco_pipeline.output.supabase_writer.requests.post")
def test_insert_kpi_values_noop_on_empty(mock_post: Mock):
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_post.return_value = mock_resp

    writer = SupabaseWriter(SupabaseAuth(url="https://example.supabase.co", service_role_key="svc"))
    writer.insert_kpi_values([])
    mock_post.assert_not_called()
