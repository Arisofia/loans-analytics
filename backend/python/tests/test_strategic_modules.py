"""Unit tests for strategic KPI module fixes and guardrails."""

import unittest

import pandas as pd

from backend.python.kpis.strategic_modules import (
    build_compliance_dashboard,
    build_pd_model,
    predict_kpis,
)


class TestStrategicModules(unittest.TestCase):
    """Validate real-data column mapping, NO_DATA semantics, and PD leakage guards."""

    def _sample_loans(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "loan_id": ["L1", "L2", "L3", "L4", "L5", "L6"],
                "outstanding_loan_value": [1000, 1500, 1200, 800, 700, 900],
                "interest_rate_apr": [0.32, 0.38, 0.41, 0.29, 0.35, 0.31],
                "term": [45, 60, 75, 40, 55, 65],
                "disbursement_amount": [1200, 1700, 1400, 1000, 900, 1100],
                "tpv": [3000, 5200, 4100, 2800, 2600, 3300],
                "days_in_default": [0, 35, 95, 10, 190, 0],
                "disbursement_date": [
                    "2025-10-05",
                    "2025-11-08",
                    "2025-12-10",
                    "2026-01-05",
                    "2026-02-01",
                    "2026-03-01",
                ],
                "pagador": ["P1", "P1", "P2", "P3", "P3", "P4"],
                "loan_status": ["Current", "Default", "Default", "Current", "Default", "Current"],
            }
        )

    def _sample_payments(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "true_payment_date": [
                    "2025-11-15",
                    "2025-12-15",
                    "2026-01-15",
                    "2026-02-15",
                    "2026-03-12",
                ],
                "true_total_payment": [350, 420, 510, 530, 490],
            }
        )

    def test_compliance_uses_days_in_default_and_pagador(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(loans, payments)

        self.assertIn("data_sources", report)
        self.assertEqual(report["data_sources"].get("par"), "loan.days_in_default")
        self.assertEqual(report["data_sources"].get("concentration"), "loan.pagador")
        self.assertEqual(report["data_sources"].get("utilization"), "NO_DATA")

        par30_row = next(row for row in report["metrics"] if row["metric"] == "par30_pct")
        self.assertNotEqual(par30_row["actual"], "NO_DATA")

    def test_compliance_marks_ce_as_no_data_without_payment_columns(self):
        loans = self._sample_loans()
        payments = pd.DataFrame({"payment_date": ["2026-01-01"]})

        report = build_compliance_dashboard(loans, payments)

        ce_row = next(row for row in report["metrics"] if row["metric"] == "ce_6m_pct")
        self.assertEqual(ce_row["status"], "no_data")
        self.assertEqual(ce_row["actual"], "NO_DATA")
        self.assertGreaterEqual(report["summary"].get("no_data", 0), 1)

    def test_pd_model_excludes_dpd_like_leakage_features(self):
        # Build enough rows for guarded CV thresholds.
        rows = []
        for i in range(120):
            defaulted = i < 45
            rows.append(
                {
                    "loan_id": f"L{i}",
                    "loan_status": "Default" if defaulted else "Current",
                    "interest_rate_apr": 0.42 if defaulted else 0.28,
                    "term": 75 if defaulted else 45,
                    "disbursement_amount": 1800 if defaulted else 1200,
                    "outstanding_loan_value": 1500 if defaulted else 900,
                    "tpv": 2200 if defaulted else 4800,
                    "days_in_default": 120 if defaulted else 0,
                }
            )
        loans = pd.DataFrame(rows)

        result = build_pd_model(loans, min_defaults=30, min_non_defaults=30, cv_folds=5)

        self.assertEqual(result.get("status"), "ok")
        features = result.get("features_used", [])
        self.assertIn("tpv", features)
        self.assertNotIn("dpd", features)
        self.assertNotIn("line_util", features)

    def test_predict_kpis_emits_data_notes(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        forecast = predict_kpis(loans, payments, horizon_months=3)

        self.assertIn("data_notes", forecast)
        self.assertIn("aum", forecast["data_notes"])
        self.assertIn("par", forecast["data_notes"])
        self.assertEqual(len(forecast["aum_forecast"]), 3)


if __name__ == "__main__":
    unittest.main()
