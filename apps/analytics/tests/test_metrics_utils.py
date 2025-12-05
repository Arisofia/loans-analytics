import unittest

import pandas as pd

from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine
from apps.analytics.src.metrics_utils import (
    debt_to_income_ratio,
    loan_to_value,
    portfolio_delinquency_rate,
    portfolio_kpis,
    weighted_portfolio_yield,
)


class TestMetricsUtils(unittest.TestCase):
    def setUp(self):
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
        kpis = portfolio_kpis(self.portfolio)
        self.assertAlmostEqual(kpis["portfolio_delinquency_rate_percent"], 25.0)
        self.assertAlmostEqual(kpis["portfolio_yield_percent"], 4.16537, places=5)
        self.assertAlmostEqual(kpis["average_ltv_ratio_percent"], 86.7708333, places=5)
        self.assertAlmostEqual(kpis["average_dti_ratio_percent"], 22.875, places=3)

    def test_metric_helpers_handle_edge_cases(self):
        data = pd.DataFrame(
            {
                "loan_amount": [100000, 0],
                "appraised_value": [0, 200000],
                "borrower_income": [0, 120000],
                "monthly_debt": [500, 2000],
                "loan_status": ["current", "90+ days past due"],
                "interest_rate": [0.04, 0.06],
                "principal_balance": [0, 500000],
            }
        )

        ltv = loan_to_value(data["loan_amount"], data["appraised_value"])
        dti = debt_to_income_ratio(data["monthly_debt"], data["borrower_income"])

        self.assertTrue(ltv.isna().iloc[0])
        self.assertAlmostEqual(ltv.iloc[1], 0.0)
        self.assertTrue(dti.isna().iloc[0])
        self.assertAlmostEqual(dti.iloc[1], 20.0)
        self.assertAlmostEqual(portfolio_delinquency_rate(data["loan_status"]), 50.0)
        self.assertAlmostEqual(weighted_portfolio_yield(data["interest_rate"], data["principal_balance"]), 6.0)

    def test_engine_uses_metric_utilities(self):
        engine = LoanAnalyticsEngine(self.portfolio)
        dashboard = engine.run_full_analysis()

        expected = portfolio_kpis(self.portfolio)
        # The engine may include extra data-quality fields; ensure the KPI set matches.
        self.assertTrue(set(expected.keys()).issubset(dashboard.keys()))
        for key in expected:
            self.assertAlmostEqual(dashboard[key], expected[key])

    def test_numeric_coercion_and_defaults(self):
        portfolio = self.portfolio.copy()
        portfolio["loan_amount"] = portfolio["loan_amount"].astype(str)
        portfolio["principal_balance"] = portfolio["principal_balance"].astype(str)

        kpis = portfolio_kpis(portfolio)

        self.assertGreater(kpis["portfolio_yield_percent"], 0)
        self.assertGreater(kpis["average_ltv_ratio_percent"], 0)


if __name__ == "__main__":
    unittest.main()
