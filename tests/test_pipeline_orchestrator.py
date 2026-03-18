from unittest.mock import MagicMock, patch

import pytest

from backend.src.pipeline.orchestrator import UnifiedPipeline


@pytest.fixture
def mock_pipeline_deps():
    with (
        patch("backend.src.pipeline.config.PipelineConfig.load") as mock_load,
        patch("backend.src.pipeline.config.load_business_rules") as mock_rules,
        patch("backend.src.pipeline.config.load_kpi_definitions") as mock_kpis,
        patch("backend.src.pipeline.orchestrator.IngestionPhase") as mock_ingestion,
        patch("backend.src.pipeline.orchestrator.TransformationPhase") as mock_trans,
        patch("backend.src.pipeline.orchestrator.CalculationPhase") as mock_calc,
        patch("backend.src.pipeline.orchestrator.OutputPhase") as mock_output,
    ):

        mock_load.return_value = MagicMock(
            ingestion={}, transformation={}, calculation={}, output={}
        )
        mock_rules.return_value = {}
        mock_kpis.return_value = {}

        yield {
            "ingestion": mock_ingestion,
            "transformation": mock_trans,
            "calculation": mock_calc,
            "output": mock_output,
        }


def test_pipeline_init(mock_pipeline_deps):
    pipeline = UnifiedPipeline()
    assert pipeline.ingestion is not None
    assert pipeline.transformation is not None
    assert pipeline.calculation is not None
    assert pipeline.output is not None


def test_pipeline_execute_full_success(mock_pipeline_deps, tmp_path):
    # Setup mocks
    mock_pipeline_deps["ingestion"].return_value.execute.return_value = {
        "status": "success",
        "output_path": "raw.csv",
    }
    mock_pipeline_deps["transformation"].return_value.execute.return_value = {
        "status": "success",
        "output_path": "clean.csv",
    }
    mock_pipeline_deps["calculation"].return_value.execute.return_value = {
        "status": "success",
        "kpis": {"par30": 5.0},
    }
    mock_pipeline_deps["output"].return_value.execute.return_value = {"status": "success"}

    pipeline = UnifiedPipeline(base_log_dir=tmp_path)
    results = pipeline.execute(mode="full")

    assert results["status"] == "success"
    assert "ingestion" in results["phases"]
    assert "transformation" in results["phases"]
    assert "calculation" in results["phases"]
    assert "output" in results["phases"]


def test_pipeline_execute_fail_at_ingestion(mock_pipeline_deps, tmp_path):
    mock_pipeline_deps["ingestion"].return_value.execute.return_value = {
        "status": "failed",
        "error": "Connection refused",
    }

    pipeline = UnifiedPipeline(base_log_dir=tmp_path)
    results = pipeline.execute(mode="full")

    assert results["status"] == "failed"
    assert "Phase 1 (Ingestion) failed" in results["error"]


def test_pipeline_dry_run(mock_pipeline_deps, tmp_path):
    mock_pipeline_deps["ingestion"].return_value.execute.return_value = {
        "status": "success",
        "output_path": "raw.csv",
    }

    pipeline = UnifiedPipeline(base_log_dir=tmp_path)
    results = pipeline.execute(mode="dry-run")

    assert results["status"] == "success"
    assert "ingestion" in results["phases"]
    assert "transformation" not in results["phases"]
    mock_pipeline_deps["transformation"].return_value.execute.assert_not_called()

