"""Tests for strategic KPI outputs in KPICatalogProcessor."""

import unittest

import pandas as pd

from backend.python.kpis.catalog_processor import KPICatalogProcessor


class TestKPICatalogProcessorStrategic(unittest.TestCase):
    """Validate forecasting, churn, prioritization, and governance outputs."""

    def setUp(self):
        self.loans_df = pd.DataFrame(
            {
                "loan_id": ["L1", "L2", "L3", "L4", "L5", "L6"],
                "customer_id": ["C1", "C2", "C3", "C4", "C5", "C6"],
                "origination_date": [
                    "2025-01-10",
                    "2025-02-12",
                    "2025-03-15",
                    "2025-04-11",
                    "2025-05-09",
                    "2025-06-18",
                ],
                "outstanding_loan_value": [12000, 14000, 16000, 15000, 18000, 19000],
                "principal_amount": [13000, 15000, 17000, 16000, 19000, 20000],
                "interest_rate_apr": [0.28, 0.26, 0.25, 0.24, 0.23, 0.22],
                "origination_fee": [200, 250, 300, 260, 320, 340],
                "origination_fee_taxes": [26, 33, 39, 34, 42, 44],
                "days_past_due": [5, 12, 18, 25, 45, 60],
                "product_type": ["SME", "SME", "Retail", "Retail", "SME", "Auto"],
                "sales_channel": ["Digital", "Digital", "KAM", "KAM", "Mixed", "Mixed"],
            }
        )

        self.payments_df = pd.DataFrame(
            {
                "payment_date": [
                    "2025-01-31",
                    "2025-02-28",
                    "2025-03-31",
                    "2025-04-30",
                    "2025-05-31",
                    "2025-06-30",
                ],
                "customer_id": ["C1", "C2", "C3", "C4", "C5", "C6"],
                "payment_amount": [1100, 1300, 1500, 1600, 1750, 1850],
                "true_interest_payment": [700, 830, 960, 1010, 1100, 1180],
                "true_fee_payment": [400, 470, 540, 590, 650, 670],
            }
        )

        self.customers_df = pd.DataFrame(
            {
                "customer_id": ["C1", "C2", "C3", "C4", "C5", "C6"],
                "created_at": [
                    "2025-01-01",
                    "2025-02-01",
                    "2025-03-01",
                    "2025-04-01",
                    "2025-05-01",
                    "2025-06-01",
                ],
                "marketing_spend": [500, 500, 600, 650, 700, 700],
            }
        )

    def test_get_all_kpis_includes_strategic_outputs(self):
        processor = KPICatalogProcessor(self.loans_df, self.payments_df, self.customers_df)
        kpis = processor.get_all_kpis()

        self.assertIn("executive_strip", kpis)
        self.assertIn("revenue_forecast_6m", kpis)
        self.assertIn("opportunity_prioritization", kpis)
        self.assertIn("unit_economics", kpis)
        self.assertIn("data_governance", kpis)
        self.assertIn("strategic_confirmations", kpis)

        strategic = kpis["strategic_confirmations"]
        self.assertTrue(strategic["cac_confirmed"])
        self.assertTrue(strategic["ltv_confirmed"])
        self.assertTrue(strategic["margin_confirmed"])
        self.assertTrue(strategic["revenue_forecast_confirmed"])

    def test_forecast_prioritization_and_governance_are_populated(self):
        processor = KPICatalogProcessor(self.loans_df, self.payments_df, self.customers_df)

        forecast_rows = processor.get_revenue_forecast()
        self.assertEqual(len(forecast_rows), 6)
        self.assertIn("forecast_revenue_usd", forecast_rows[0])

        opportunities = processor.get_opportunity_prioritization()
        self.assertGreater(len(opportunities), 0)
        self.assertIn("priority_score", opportunities[0])

        governance = processor.get_data_governance()
        self.assertIn("quality_score", governance)
        self.assertGreaterEqual(governance["quality_score"], 0.0)
        self.assertLessEqual(governance["quality_score"], 1.0)


if __name__ == "__main__":
    unittest.main()

