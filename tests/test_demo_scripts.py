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

    def test_demo_financial_analysis_with_file(self):
        """Test that the script attempts to load a file if provided."""
        with patch("sys.argv", ["script_name", "--data", "dummy.csv"]), \
             patch("scripts.demo_financial_analysis.Path.exists", return_value=True), \
             patch("scripts.demo_financial_analysis.pd.read_csv") as mock_read, \
             patch("scripts.demo_financial_analysis.plt") as mock_plt, \
             patch("builtins.print"):
            
            # Mock dataframe with minimal required columns for analysis
            mock_df = MagicMock()
            mock_df.__len__.return_value = 5
            mock_df.columns = ["outstanding_balance", "apr"]
            mock_read.return_value = mock_df
            
            main()
            mock_read.assert_called_once()
            # Verify plotting was attempted (even if columns missing in mock, logic runs)
            # Note: In this specific mock setup, 'dpd_bucket' isn't in columns, so plot might skip.
            # To test plotting specifically, we'd need a richer mock_df.