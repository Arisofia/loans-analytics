import json
import pandas as pd
from pathlib import Path

from src.pipeline.output import UnifiedOutput, PersistContext


def test_dashboard_trigger_on_persist(monkeypatch, tmp_path):
    # Arrange: create a simple df and metrics
    df = pd.DataFrame({"a": [1, 2, 3]})
    metrics = {"AUM": {"current_value": 100.0, "status": "ok"}}
    metadata = {"transformation": {}, "calculation": {}}
    run_ids = {"pipeline": "test_run_123"}

    # Configure a pipeline outputs config with dashboard_triggers enabled
    config = {
        "outputs": {
            "storage": {"local_dir": str(tmp_path / "metrics"), "manifest_dir": str(tmp_path / "runs")},
            "formats": ["json"],
            "dashboard_triggers": {"enabled": True, "outputs": ["figma", "azure"]},
        }
    }

    # Monkeypatch UnifiedOutputManager.export_kpi_metrics_only to avoid external calls
    called = {}

    def fake_export(self, kpi_metrics, run_id, enabled_outputs=None):
        called['kpi_metrics'] = kpi_metrics
        called['run_id'] = run_id
        called['outputs'] = enabled_outputs
        return {"success": True, "outputs": {o: {"success": True} for o in (enabled_outputs or [])}}

    monkeypatch.setattr("src.integrations.unified_output_manager.UnifiedOutputManager.export_kpi_metrics_only", fake_export)

    # Note: UnifiedOutput expects the 'outputs' dict directly under pipeline.phases.outputs
    uo = UnifiedOutput({"pipeline": {"phases": {"outputs": config["outputs"]}}}, run_id=run_ids["pipeline"])

    # Act
    result = uo.persist(df, metrics, metadata, run_ids)

    # Assert: manifest contains triggers.dashboard_trigger with success
    manifest = result.manifest
    assert "triggers" in manifest
    assert "dashboard_trigger" in manifest["triggers"]
    assert manifest["triggers"]["dashboard_trigger"]["success"] is True
    assert called['run_id'] == run_ids['pipeline']
    assert 'figma' in called['outputs'] and 'azure' in called['outputs']
