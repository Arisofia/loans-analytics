import unittest
from unittest.mock import patch
from scripts.demo_financial_analysis import main

class TestDemoScripts(unittest.TestCase):
    def test_demo_financial_analysis_runs(self):
        """
        Smoke test for the financial analysis demo script.
        Ensures it runs to completion without error using internal sample data.
        """
        with patch("builtins.print"):
            try:
                main()
            except Exception as e:
                self.fail(f"demo_financial_analysis.main() raised {e} unexpectedly!")