import unittest
from datetime import date, timedelta

import pandas as pd

from python.financial_analysis import FinancialAnalyzer


class TestFinancialAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = FinancialAnalyzer()

    def test_classify_dpd_buckets(self):
        data = {"days_past_due": [0, 15, 45, 75, 100, 130, 160, 200, -5]}
        df = pd.DataFrame(data)
        result = self.analyzer.classify_dpd_buckets(df)

        expected = [
            "Current",
            "1-29",
            "30-59",
            "60-89",
            "90-119",
            "120-149",
            "150-179",
            "180+",
            "Current",
        ]
        self.assertListEqual(result["dpd_bucket"].tolist(), expected)

    def test_classify_dpd_buckets_fuzzy(self):
        # Test with 'DPD' (uppercase) instead of 'days_past_due'
        data = {"DPD": [0, 45, 200]}
        df = pd.DataFrame(data)
        result = self.analyzer.classify_dpd_buckets(df)
        self.assertListEqual(result["dpd_bucket"].tolist(), ["Current", "30-59", "180+"])

    def test_calculate_weighted_stats(self):
        data = {"outstanding_balance": [1000, 2000, 3000], "apr": [0.10, 0.12, 0.15]}
        df = pd.DataFrame(data)
        result = self.analyzer.calculate_weighted_stats(df, metrics=["apr"])

        # Weighted Average: (1000*0.10 + 2000*0.12 + 3000*0.15) / 6000
        # (100 + 240 + 450) / 6000 = 790 / 6000 = 0.131666...
        expected_apr = 0.13166666666666665
        self.assertAlmostEqual(result["weighted_apr"][0], expected_apr, places=4)

    def test_segment_clients_by_exposure(self):
        data = {"outstanding_balance": [500, 5000, 50000]}
        df = pd.DataFrame(data)
        result = self.analyzer.segment_clients_by_exposure(df)

        expected = ["Micro", "Small", "Medium/Large"]
        self.assertListEqual(result["exposure_segment"].tolist(), expected)

    def test_segment_clients_by_exposure_fuzzy(self):
        # Test with 'Balance' instead of 'outstanding_balance'
        data = {"Balance": [500, 50000]}
        df = pd.DataFrame(data)
        result = self.analyzer.segment_clients_by_exposure(df)
        self.assertListEqual(result["exposure_segment"].tolist(), ["Micro", "Medium/Large"])

    def test_classify_client_type(self):
        today = date(2025, 1, 1)
        data = {
            "customer_id": [1, 2, 3],
            "loan_count": [1, 5, 5],
            "last_active_date": [
                today,  # New (loan_count=1)
                today - timedelta(days=30),  # Recurring (active <= 90 days)
                today - timedelta(days=100),  # Recovered (active > 90 days)
            ],
        }
        df = pd.DataFrame(data)
        result = self.analyzer.classify_client_type(df, reference_date=today)

        expected = ["New", "Recurring", "Recovered"]
        self.assertListEqual(result["client_type"].tolist(), expected)

    def test_calculate_line_utilization(self):
        data = {"line_amount": [10000, 10000, 10000], "outstanding_balance": [5000, 12000, 0]}
        df = pd.DataFrame(data)
        result = self.analyzer.calculate_line_utilization(df)

        # 0.5, 1.0 (capped), 0.0
        expected = [0.5, 1.0, 0.0]
        self.assertListEqual(result["line_utilization"].tolist(), expected)

    def test_calculate_hhi(self):
        # 2 customers with equal exposure -> 0.5^2 + 0.5^2 = 0.25 + 0.25 = 0.5 -> HHI 5000
        data = {"customer_id": ["A", "B"], "outstanding_balance": [100, 100]}
        df = pd.DataFrame(data)
        hhi = self.analyzer.calculate_hhi(df, "customer_id")
        self.assertEqual(hhi, 5000.0)

    def test_calculate_hhi_fuzzy(self):
        # Test with 'Client_ID' and 'Balance' instead of defaults
        data = {"Client_ID": ["A", "B"], "Balance": [100, 100]}
        df = pd.DataFrame(data)
        hhi = self.analyzer.calculate_hhi(df)
        self.assertEqual(hhi, 5000.0)

    def test_enrich_master_dataframe(self):
        today = date(2025, 1, 1)
        data = {
            "loan_id": [1, 2],
            "customer_id": ["C1", "C2"],
            "outstanding_balance": [5000, 15000],
            "line_amount": [10000, 20000],
            "days_past_due": [10, 45],
            "loan_count": [1, 5],
            "last_active_date": [today, today],
            "apr": [0.15, 0.12],
        }
        df = pd.DataFrame(data)
        result = self.analyzer.enrich_master_dataframe(df, reference_date=today)

        self.assertIn("dpd_bucket", result.columns)
        self.assertIn("exposure_segment", result.columns)
        self.assertIn("client_type", result.columns)
        self.assertIn("line_utilization", result.columns)
        self.assertIn("apr_zscore", result.columns)


if __name__ == "__main__":
    unittest.main()
