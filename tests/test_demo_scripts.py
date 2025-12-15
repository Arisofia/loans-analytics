import unittest
import sys
from unittest.mock import patch, MagicMock
from scripts.demo_financial_analysis import main

class TestDemoScripts(unittest.TestCase):
    def test_demo_financial_analysis_runs(self):
        """
        Smoke test for the financial analysis demo script.
        Ensures it runs to completion without error using internal sample data.
        """
        # Simulate no arguments
        with patch("sys.argv", ["script_name"]), patch("builtins.print"), patch("scripts.demo_financial_analysis.plt"):
            try:
                main()
            except Exception as e:
                self.fail(f"demo_financial_analysis.main() raised {e} unexpectedly!")

    @patch("scripts.demo_financial_analysis.FinancialAnalyzer")
    def test_demo_financial_analysis_with_file(self, mock_analyzer_cls):
        """Test that the script attempts to load a file if provided."""
        with patch("sys.argv", ["script_name", "--data", "dummy.csv"]), \
             patch("scripts.demo_financial_analysis.Path.exists", return_value=True), \
             patch("scripts.demo_financial_analysis.pd.read_csv") as mock_read, \
             patch("scripts.demo_financial_analysis.plt") as mock_plt, \
             patch("builtins.print"):
            
            # Setup mocks
            mock_read.return_value = MagicMock()
            
            mock_analyzer = mock_analyzer_cls.return_value
            # Mock enriched_df to have the columns we need for plotting
            mock_enriched = MagicMock()
            # Ensure columns check passes for visualization
            mock_enriched.columns = ["loan_id", "dpd_bucket", "exposure_segment"]
            mock_analyzer.enrich_master_dataframe.return_value = mock_enriched
            mock_analyzer.calculate_hhi.return_value = 5000.0
            
            main()
            mock_read.assert_called_once()
            
            # Verify plotting was attempted for both DPD and Exposure
            # We expect 2 figures and 2 saves
            self.assertEqual(mock_plt.figure.call_count, 2)
            self.assertEqual(mock_plt.savefig.call_count, 2)

    @patch("scripts.demo_financial_analysis.FinancialAnalyzer")
    def test_demo_financial_analysis_skips_plots_if_columns_missing(self, mock_analyzer_cls):
        """Test that the script skips plotting if columns are missing."""
        with patch("sys.argv", ["script_name", "--data", "dummy.csv"]), \
             patch("scripts.demo_financial_analysis.Path.exists", return_value=True), \
             patch("scripts.demo_financial_analysis.pd.read_csv") as mock_read, \
             patch("scripts.demo_financial_analysis.plt") as mock_plt, \
             patch("builtins.print"):
            
            # Setup mocks
            mock_read.return_value = MagicMock()
            
            mock_analyzer = mock_analyzer_cls.return_value
            # Mock enriched_df missing 'dpd_bucket' and 'exposure_segment'
            mock_enriched = MagicMock()
            # Ensure columns check fails for visualization
            mock_enriched.columns = ["loan_id"]
            mock_analyzer.enrich_master_dataframe.return_value = mock_enriched
            mock_analyzer.calculate_hhi.return_value = 5000.0
            
            main()
            
            mock_read.assert_called_once()
            
            # Verify plotting was NOT attempted
            self.assertEqual(mock_plt.figure.call_count, 0)
            self.assertEqual(mock_plt.savefig.call_count, 0)