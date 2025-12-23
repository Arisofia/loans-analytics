import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from scripts.run_data_pipeline import run_pipeline


class TestRunDataPipeline(unittest.TestCase):
    @patch("scripts.run_data_pipeline.write_compliance_report")
    @patch("scripts.run_data_pipeline.build_compliance_report")
    @patch("scripts.run_data_pipeline.write_outputs")
    @patch("scripts.run_data_pipeline.KPIEngine")
    @patch("scripts.run_data_pipeline.DataTransformation")
    @patch("scripts.run_data_pipeline.CascadeIngestion")
    def test_run_pipeline_success(self, mock_ingest_cls, mock_transform_cls, mock_kpi_cls, mock_write_outputs, mock_build_report, mock_write_report):
        mock_ingest = mock_ingest_cls.return_value
        mock_ingest.run_id = "test_run"
        ingest_df = pd.DataFrame({"period": ["2025Q4"], "_validation_passed": [True]})
        mock_ingest.ingest_csv.return_value = ingest_df.copy()
        mock_ingest.validate_loans.return_value = ingest_df.copy()
        mock_ingest.errors = []
        mock_ingest.raw_files = [{"file": "dummy.csv", "status": "ingested", "rows": 1, "timestamp": "now"}]
        mock_ingest.get_ingest_summary.return_value = {"rows": 1}

        mock_transform = mock_transform_cls.return_value
        mock_transform.transform_to_kpi_dataset.return_value = pd.DataFrame({"metric": [1.0]})
        mock_transform.get_processing_summary.return_value = {"processed": True}
        mock_transform.get_lineage.return_value = []

        mock_kpi = mock_kpi_cls.return_value
        mock_kpi.calculate_par_30.return_value = (1.0, {"metric": "PAR30"})
        mock_kpi.calculate_par_90.return_value = (0.5, {"metric": "PAR90"})
        mock_kpi.calculate_collection_rate.return_value = (98.0, {"metric": "CR"})
        mock_kpi.calculate_portfolio_health.return_value = (9.0, {"metric": "Health"})
        mock_kpi.get_audit_trail.return_value = MagicMock(to_dict=lambda **k: [])

        processed_paths = {
            "metrics_file": "metrics.parquet",
            "csv_file": "metrics.csv",
            "manifest_file": "manifest.json",
            "compliance_report_file": "compliance.json",
            "generated_at": "now",
        }
        mock_write_outputs.return_value = processed_paths
        mock_build_report.return_value = {}

        result = run_pipeline("dummy.csv")

        self.assertTrue(result)
        mock_ingest.ingest_csv.assert_called()
        mock_transform.transform_to_kpi_dataset.assert_called()
        mock_kpi.calculate_portfolio_health.assert_called()
        mock_write_outputs.assert_called()

    @patch("scripts.run_data_pipeline.CascadeIngestion")
    def test_run_pipeline_validation_failure(self, mock_ingest_cls):
        mock_ingest = mock_ingest_cls.return_value
        mock_ingest.run_id = "test_run"
        failing_df = pd.DataFrame({"period": ["2025Q4"], "_validation_passed": [False]})
        mock_ingest.ingest_csv.return_value = failing_df.copy()
        mock_ingest.validate_loans.return_value = failing_df.copy()
        mock_ingest.errors = [{"stage": "validation", "error": "failed"}]
        mock_ingest.raw_files = [{"file": "dummy.csv", "status": "ingested", "rows": 1, "timestamp": "now"}]
        mock_ingest.get_ingest_summary.return_value = {"rows": 1}

        result = run_pipeline("dummy.csv")

        self.assertFalse(result)

    @patch("scripts.run_data_pipeline.rewrite_manifest")
    @patch("scripts.run_data_pipeline.upload_outputs_to_azure")
    @patch("scripts.run_data_pipeline.write_compliance_report")
    @patch("scripts.run_data_pipeline.build_compliance_report")
    @patch("scripts.run_data_pipeline.write_outputs")
    @patch("scripts.run_data_pipeline.KPIEngine")
    @patch("scripts.run_data_pipeline.DataTransformation")
    @patch("scripts.run_data_pipeline.CascadeIngestion")
    def test_run_pipeline_exports_to_azure(
        self,
        mock_ingest_cls,
        mock_transform_cls,
        mock_kpi_cls,
        mock_write_outputs,
        mock_build_report,
        mock_write_report,
        mock_upload,
        mock_rewrite_manifest,
    ):
        mock_ingest = mock_ingest_cls.return_value
        mock_ingest.run_id = "test_run"
        df = pd.DataFrame({"period": ["2025Q4"], "_validation_passed": [True]})
        mock_ingest.ingest_csv.return_value = df.copy()
        mock_ingest.validate_loans.return_value = df.copy()
        mock_ingest.errors = []
        mock_ingest.raw_files = [{"file": "dummy.csv", "status": "ingested", "rows": 1, "timestamp": "now"}]
        mock_ingest.get_ingest_summary.return_value = {"rows": 1}

        mock_transform = mock_transform_cls.return_value
        mock_transform.transform_to_kpi_dataset.return_value = pd.DataFrame({"metric": [1.0]})
        mock_transform.get_processing_summary.return_value = {"processed": True}
        mock_transform.get_lineage.return_value = []

        mock_kpi = mock_kpi_cls.return_value
        mock_kpi.calculate_par_30.return_value = (1.0, {"metric": "PAR30"})
        mock_kpi.calculate_par_90.return_value = (0.5, {"metric": "PAR90"})
        mock_kpi.calculate_collection_rate.return_value = (98.0, {"metric": "CR"})
        mock_kpi.calculate_portfolio_health.return_value = (9.0, {"metric": "Health"})
        mock_kpi.get_audit_trail.return_value = MagicMock(to_dict=lambda **k: [])

        processed_paths = {
            "metrics_file": "metrics.parquet",
            "csv_file": "metrics.csv",
            "manifest_file": "manifest.json",
            "compliance_report_file": "compliance.json",
            "generated_at": "now",
        }
        mock_write_outputs.return_value = processed_paths
        mock_build_report.return_value = {}
        mock_upload.return_value = {"metrics_file": "container/metrics.parquet"}

        result = run_pipeline(
            "dummy.csv",
            azure_container="container",
            azure_connection_string="UseDevelopmentStorage=true",
            azure_blob_prefix="runs",
        )

        self.assertTrue(result)
        mock_upload.assert_called_once()
        mock_rewrite_manifest.assert_called_once()
