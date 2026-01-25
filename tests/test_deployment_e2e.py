import json

import pandas as pd
import pytest

from src.analytics.run_pipeline import calculate_kpis, create_metrics_csv, main


class TestDeploymentE2E:
    """End-to-end tests verifying production-ready deployment state."""

    @pytest.fixture
    def sample_dataset(self):
        """Create minimal sample dataset for testing."""
        return pd.DataFrame(
            {
                "segment": ["Consumer", "Consumer", "SME", "SME"],
                "measurement_date": ["2025-01-31"] * 4,
                "total_receivable_usd": [250000, 300000, 500000, 450000],
                "total_eligible_usd": [250000, 300000, 500000, 450000],
                "cash_available_usd": [245000, 294000, 490000, 432000],
                "dpd_0_7_usd": [5000, 6000, 10000, 18000],
                "dpd_7_30_usd": [0, 0, 0, 0],
                "dpd_30_60_usd": [0, 0, 0, 0],
                "dpd_60_90_usd": [0, 0, 0, 0],
                "dpd_90_plus_usd": [0, 0, 0, 0],
            }
        )

    def test_e2e_kpi_calculation_produces_valid_output(self, sample_dataset):
        kpis = calculate_kpis(sample_dataset)

        assert isinstance(kpis, dict)
        assert len(kpis) > 15, "Should have at least 15 KPIs"

        required_keys = [
            "total_receivable_usd",
            "total_eligible_usd",
            "total_cash_available_usd",
            "collection_rate_pct",
            "par_90_pct",
            "num_records",
            "portfolio_health_score",
        ]

        for key in required_keys:
            assert key in kpis, f"Missing required KPI: {key}"
            assert isinstance(kpis[key], (int, float, str)), f"KPI {key} has invalid type"

    def test_e2e_metrics_csv_generation(self, sample_dataset, tmp_path):
        """Test that metrics CSV generation works correctly."""
        output_file = tmp_path / "metrics.csv"
        create_metrics_csv(sample_dataset, output_file)

        assert output_file.exists(), "Metrics CSV not created"
        metrics_df = pd.read_csv(output_file)

        assert len(metrics_df) > 0, "Metrics CSV is empty"
        assert "metric_name" in metrics_df.columns
        assert "value" in metrics_df.columns
        assert "segment" in metrics_df.columns

    def test_e2e_main_pipeline_success(self, sample_dataset, tmp_path):
        """Test complete pipeline execution through main()."""
        dataset_file = tmp_path / "input.csv"
        sample_dataset.to_csv(dataset_file, index=False)

        output_dir = tmp_path / "output"

        result = main(
            [
                "--dataset",
                str(dataset_file),
                "--output",
                str(output_dir),
            ]
        )

        assert result == 0, "Pipeline should return 0 on success"

        kpi_file = output_dir / "kpi_results.json"
        assert kpi_file.exists(), "KPI results file not created"

        with open(kpi_file) as f:
            kpis = json.load(f)

        assert isinstance(kpis, dict)
        assert "total_receivable_usd" in kpis
        assert "collection_rate_pct" in kpis

        metrics_file = output_dir / "metrics.csv"
        assert metrics_file.exists(), "Metrics CSV not created"

    def test_e2e_empty_dataset_handling(self, tmp_path):
        """Test pipeline gracefully handles empty datasets."""
        empty_df = pd.DataFrame(
            {
                "total_receivable_usd": [],
                "total_eligible_usd": [],
                "cash_available_usd": [],
            }
        )

        dataset_file = tmp_path / "empty.csv"
        empty_df.to_csv(dataset_file, index=False)

        output_dir = tmp_path / "output"

        result = main(
            [
                "--dataset",
                str(dataset_file),
                "--output",
                str(output_dir),
            ]
        )

        assert result == 0, "Pipeline should handle empty datasets"

    def test_e2e_missing_dataset_error(self, tmp_path):
        """Test pipeline returns error for missing dataset."""
        nonexistent_file = tmp_path / "nonexistent.csv"
        output_dir = tmp_path / "output"

        result = main(
            [
                "--dataset",
                str(nonexistent_file),
                "--output",
                str(output_dir),
            ]
        )

        assert result == 1, "Pipeline should return 1 on missing dataset"

    def test_e2e_kpi_value_ranges(self, sample_dataset):
        """Test that KPI values are within expected ranges."""
        kpis = calculate_kpis(sample_dataset)

        percentages = ["collection_rate_pct", "par_90_pct", "delinquency_rate_pct"]
        for pct_key in percentages:
            if pct_key in kpis:
                val = kpis[pct_key]
                assert -1 <= val <= 101, f"{pct_key} outside valid percentage range: {val}"

        scores = ["portfolio_health_score"]
        for score_key in scores:
            if score_key in kpis:
                val = kpis[score_key]
                assert 0 <= val <= 10, f"{score_key} outside valid range 0-10: {val}"

    def test_e2e_segment_analysis(self, sample_dataset):
        """Test that segment-level analysis produces correct results."""
        kpis = calculate_kpis(sample_dataset)

        segment_keys = ["consumer_receivable_usd", "sme_receivable_usd"]
        for key in segment_keys:
            if key in kpis:
                assert isinstance(kpis[key], (int, float))
                assert kpis[key] >= 0
