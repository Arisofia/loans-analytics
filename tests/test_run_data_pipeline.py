import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_data_pipeline import main


class TestRunDataPipeline(unittest.TestCase):
    @patch("scripts.run_data_pipeline.UnifiedPipeline")
    def test_run_pipeline_success(self, mock_pipeline_cls):
        mock_pipeline = mock_pipeline_cls.return_value
        mock_pipeline.execute.return_value = {
            "status": "success",
            "run_id": "test_run_123",
        }

        result = main(input_file="data/test.csv")

        self.assertTrue(result)
        mock_pipeline_cls.assert_called_once()
        mock_pipeline.execute.assert_called_once()

    @patch("scripts.run_data_pipeline.UnifiedPipeline")
    def test_run_pipeline_failure(self, mock_pipeline_cls):
        mock_pipeline = mock_pipeline_cls.return_value
        mock_pipeline.execute.return_value = {
            "status": "failed",
            "run_id": "test_run_456",
        }

        result = main(input_file="data/test.csv")

        self.assertFalse(result)
        mock_pipeline.execute.assert_called_once()

    @patch("scripts.run_data_pipeline.UnifiedPipeline")
    def test_run_pipeline_with_error(self, mock_pipeline_cls):
        mock_pipeline = mock_pipeline_cls.return_value
        mock_pipeline.execute.side_effect = Exception("Pipeline error")

        result = main(input_file="data/test.csv")

        self.assertFalse(result)

    @patch("scripts.run_data_pipeline.UnifiedPipeline")
    def test_run_pipeline_with_custom_config(self, mock_pipeline_cls):
        mock_pipeline = mock_pipeline_cls.return_value
        mock_pipeline.execute.return_value = {
            "status": "success",
            "run_id": "test_run_789",
        }

        result = main(
            input_file="data/test.csv",
            user="test_user",
            action="test_action",
            config_path="config/test.yml",
        )

        self.assertTrue(result)
        mock_pipeline_cls.assert_called_once_with(config_path=Path("config/test.yml"))
