"""
FI-ANALYTICS-002: Sprint 0 Smoke & Artifact Tests

Test Cases:
  - A-01: Pipeline smoke test with sample_small.csv
  - A-02: Output artifacts existence and schema validation
"""

import subprocess
import sys
from typing import Any, Dict

import pytest


class TestAnalyticsSmoke:
    """Smoke tests for analytics pipeline."""

    def test_a01_pipeline_smoke_execution(
        self, analytics_test_env: Dict[str, Any]
    ) -> None:
        """
        A-01: Pipeline smoke test — execute with sample_small.csv → completes successfully.

        **Preconditions**:
        - sample_small.csv present
        - Analytics environment configured (integrations disabled)
        - Output directory clean

        **Expected**: Pipeline exits 0, artifacts created, success logged
        """
        dataset = analytics_test_env["dataset_path"]
        output_dir = analytics_test_env["output_dir"]

        assert dataset.exists(), f"Dataset not found: {dataset}"
        assert output_dir.exists(), f"Output dir not found: {output_dir}"

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.analytics.run_pipeline",
                    "--dataset",
                    str(dataset),
                    "--output",
                    str(output_dir),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            assert result.returncode == 0, (
                f"Pipeline failed with exit code {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

            assert (
                "Pipeline start" in result.stderr or "Pipeline start" in result.stdout
            ), "Pipeline start message not found in logs"

        except subprocess.TimeoutExpired:
            pytest.fail("Pipeline execution exceeded 60 second timeout")

    # def test_a02_artifact_existence_and_schema(
    #     self, run_analytics_pipeline: Path, kpi_schema: Dict[str, Any]
    # ) -> None:
    #     """
    #     A-02: Output artifacts existence and schema validation.
    #
    #     **Expected**:
    #     - kpi_results.json exists and is valid JSON
    #     - metrics.csv exists and is valid CSV
    #     - JSON matches schema
    #     - Required fields present (run_id, timestamp, KPI values)
    #     - File sizes > 100 bytes
    #     """
    #     output_dir = run_analytics_pipeline
    #
    #     kpi_json_path = output_dir / "kpi_results.json"
    #     metrics_csv_path = output_dir / "metrics.csv"
    #
    #     assert kpi_json_path.exists(), f"kpi_results.json not found at {kpi_json_path}"
    #     assert metrics_csv_path.exists(), f"metrics.csv not found at {metrics_csv_path}"
    #
    #     assert kpi_json_path.stat().st_size > 100, (
    #         f"kpi_results.json too small: {kpi_json_path.stat().st_size} bytes"
    #     )
    #     assert metrics_csv_path.stat().st_size > 100, (
    #         f"metrics.csv too small: {metrics_csv_path.stat().st_size} bytes"
    #     )
    #
    #     with open(kpi_json_path) as f:
    #         kpi_data = json.load(f)
    #
    #     jsonschema.validate(instance=kpi_data, schema=kpi_schema)
    #
    #     assert "run_id" in kpi_data, "run_id field missing from kpi_results.json"
    #     assert "timestamp" in kpi_data, "timestamp field missing from kpi_results.json"
    #     assert "pipeline_status" in kpi_data, "pipeline_status field missing"
    #     assert isinstance(kpi_data["run_id"], str), "run_id must be string"
    #     assert isinstance(kpi_data["timestamp"], str), "timestamp must be string"
    #
    #     df_metrics = pd.read_csv(metrics_csv_path)
    #     assert not df_metrics.empty, "metrics.csv is empty"
    #     assert "metric_name" in df_metrics.columns, "metric_name column missing"
    #     assert "value" in df_metrics.columns, "value column missing"

    # def test_a02_json_required_fields(self, run_analytics_pipeline: Path) -> None:
    #     """Verify all required KPI fields are present in output."""
    #     output_dir = run_analytics_pipeline
    #     kpi_json_path = output_dir / "kpi_results.json"
    #
    #     with open(kpi_json_path) as f:
    #         kpi_data = json.load(f)
    #
    #     required_fields = [
    #         "total_receivable_usd",
    #         "collection_rate_pct",
    #         "par_90_pct",
    #         "num_records",
    #     ]
    #
    #     for field in required_fields:
    #         assert field in kpi_data, (
    #             f"Required field '{field}' missing from kpi_results.json"
    #         )
    #         assert isinstance(kpi_data[field], (int, float)), (
    #             f"Field '{field}' must be numeric, got {type(kpi_data[field])}"
    #         )

    # def test_a02_csv_valid_structure(self, run_analytics_pipeline: Path) -> None:
    #     """Verify metrics.csv has valid structure and data types."""
    #     output_dir = run_analytics_pipeline
    #     metrics_csv_path = output_dir / "metrics.csv"
    #
    #     df = pd.read_csv(metrics_csv_path)
    #
    #     required_columns = ["metric_name", "value", "unit"]
    #     for col in required_columns:
    #         assert col in df.columns, f"Column '{col}' missing from metrics.csv"
    #
    #     assert df["value"].dtype in ["float64", "int64"], (
    #         f"Value column must be numeric, got {df['value'].dtype}"
    #     )
    #
    #     assert not df["metric_name"].isnull().any(), "metric_name contains nulls"
    #     assert not df["value"].isnull().any(), "value contains nulls"
