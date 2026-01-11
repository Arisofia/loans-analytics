import json
import logging
import os
from pathlib import Path

import pytest


def test_batch_export_load_latest_metrics_invalid_json(tmp_path, caplog, monkeypatch):
    # Arrange: create data/metrics/latest_metrics.json with a non-dict JSON value
    metrics_dir = tmp_path / "data" / "metrics"
    metrics_dir.mkdir(parents=True)
    metrics_file = metrics_dir / "latest_metrics.json"
    metrics_file.write_text(json.dumps(["not", "a", "dict"]))

    # Run from tmp_path so relative paths in the implementation resolve there
    monkeypatch.chdir(tmp_path)

    from src.integrations.batch_export_runner import BatchExportRunner

    caplog.set_level(logging.ERROR)

    # Act
    runner = BatchExportRunner()
    data = runner.load_latest_metrics()

    # Assert
    assert data == {}
    assert any(
        "Expected dict" in rec.message or "Failed to parse" in rec.message for rec in caplog.records
    )


def test_load_dashboard_metrics_invalid_json(tmp_path, caplog, capsys, monkeypatch):
    # Arrange: create a malformed dashboard JSON file and point the module constant to it
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir(parents=True)
    dashboard_file = exports_dir / "complete_kpi_dashboard.json"
    dashboard_file.write_text("123")  # valid JSON but not a dict

    import src.analytics_metrics as analytics_metrics

    monkeypatch.setattr(analytics_metrics, "DASHBOARD_JSON", dashboard_file)

    caplog.set_level(logging.ERROR)

    # Act
    data = analytics_metrics.load_dashboard_metrics()

    # Assert
    assert data == {}

    # Prefer caplog, but fall back to captured stderr if the message was emitted
    if not any(
        "Expected dict" in rec.message or "Failed to parse" in rec.message for rec in caplog.records
    ):
        captured = capsys.readouterr()
        assert "Expected dict" in captured.err or "Failed to parse" in captured.err
