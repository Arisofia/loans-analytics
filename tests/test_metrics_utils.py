"""
Unit tests for metrics utility functions in the analytics engine.
"""

import unittest

import pandas as pd

from src.analytics.enterprise_analytics_engine import LoanAnalyticsEngine
from src.analytics.metrics_utils import (debt_to_income_ratio, loan_to_value,
                                         portfolio_delinquency_rate,
                                         portfolio_kpis,
                                         weighted_portfolio_yield)


class TestMetricsUtils(unittest.TestCase):
    """Unit tests for metrics utility functions."""

    def setUp(self):
        """Set up a sample portfolio DataFrame for use in all test cases."""
        self.portfolio = pd.DataFrame(
            {
                "loan_amount": [250000, 450000, 150000, 600000],
                "appraised_value": [300000, 500000, 160000, 750000],
                "borrower_income": [80000, 120000, 60000, 150000],
                "monthly_debt": [1500, 2500, 1000, 3000],
                "loan_status": ["current", "30-59 days past due", "current", "current"],
                "interest_rate": [0.035, 0.042, 0.038, 0.045],
                "principal_balance": [240000, 440000, 145000, 590000],
            }
        )

    def test_kpis_match_expected_values(self):
        """
        Test that portfolio_kpis returns expected KPI values for a sample
        portfolio.
        """
        kpis, _ = portfolio_kpis(self.portfolio)
        self.assertAlmostEqual(kpis["portfolio_delinquency_rate_percent"], 25.0)

    def test_numeric_coercion_and_defaults(self):
        """
        Test numeric coercion and default handling for loan_amount and
        principal_balance columns.
        """
        portfolio = self.portfolio.copy()
        portfolio["loan_amount"] = portfolio["loan_amount"].astype(str)
        portfolio["principal_balance"] = portfolio["principal_balance"].astype(str)

        kpis, _ = portfolio_kpis(portfolio)

        self.assertGreater(kpis["portfolio_yield_percent"], 0)

    def test_engine_uses_metric_utilities(self):
        """
        Test that LoanAnalyticsEngine uses metric utilities and returns
        expected KPI keys.
        """
        engine = LoanAnalyticsEngine(self.portfolio)
        dashboard = engine.run_full_analysis()

        expected, _ = portfolio_kpis(self.portfolio)
        # Verify that all expected keys are present in dashboard
        for key in expected:
            self.assertIn(key, dashboard)


if __name__ == "__main__":
    unittest.main()
