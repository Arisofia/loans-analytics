import unittest
from unittest.mock import MagicMock, patch
from scripts.run_data_pipeline import run_pipeline

class TestRunDataPipeline(unittest.TestCase):
    @patch("scripts.run_data_pipeline.CascadeIngestion")
    @patch("scripts.run_data_pipeline.DataTransformation")
    @patch("scripts.run_data_pipeline.KPIEngine")
    @patch("scripts.run_data_pipeline.write_outputs")
    def test_run_pipeline_success(self, mock_write, mock_kpi_cls, mock_transform_cls, mock_ingest_cls):
        # Setup Mocks
        mock_ingest = mock_ingest_cls.return_value
        mock_ingest.run_id = "test_run"
        mock_ingest.ingest_csv.return_value = MagicMock(empty=False)
        # Validation passes
        mock_ingest.validate_loans.return_value.__getitem__.return_value.all.return_value = True
        mock_ingest.get_ingest_summary.return_value = {"rows": 10}
        
        mock_transform = mock_transform_cls.return_value
        mock_transform.transform_to_kpi_dataset.return_value = MagicMock()
        mock_transform.run_id = "tx_run"
        
        mock_kpi = mock_kpi_cls.return_value
        mock_kpi.calculate_par_30.return_value = (1.0, {"metric": "PAR30"})
        mock_kpi.calculate_par_90.return_value = (0.5, {"metric": "PAR90"})
        mock_kpi.calculate_collection_rate.return_value = (98.0, {"metric": "CR"})
        mock_kpi.calculate_portfolio_health.return_value = (9.0, {"metric": "Health"})
        mock_kpi.get_audit_trail.return_value = MagicMock(to_dict=lambda **k: [])

        # Execute
        result = run_pipeline("dummy.csv")
        
        # Verify
        self.assertTrue(result)
        mock_ingest.ingest_csv.assert_called()
        mock_transform.transform_to_kpi_dataset.assert_called()
        mock_kpi.calculate_portfolio_health.assert_called()
        mock_write.assert_called()

    @patch("scripts.run_data_pipeline.CascadeIngestion")
    def test_run_pipeline_validation_failure(self, mock_ingest_cls):
        mock_ingest = mock_ingest_cls.return_value
        mock_ingest.ingest_csv.return_value = MagicMock(empty=False)
        # Validation fails
        mock_ingest.validate_loans.return_value.__getitem__.return_value.all.return_value = False
        
        result = run_pipeline("dummy.csv")
        
        self.assertFalse(result)