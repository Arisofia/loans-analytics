"""Unit tests for strategic KPI module fixes and guardrails."""

import unittest

import pandas as pd

from backend.python.kpis.strategic_modules import (
    build_compliance_dashboard,
    build_next_steps_plan,
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

    def test_compliance_marks_utilization_as_no_data_when_line_missing(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(loans, payments)

        util_row = next(row for row in report["metrics"] if row["metric"] == "utilization_pct")
        self.assertEqual(util_row["status"], "no_data")
        self.assertEqual(util_row["actual"], "NO_DATA")

    def test_compliance_marks_dscr_as_no_data_when_inputs_missing(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(loans, payments)

        dscr_row = next(row for row in report["metrics"] if row["metric"] == "dscr")
        self.assertEqual(dscr_row["status"], "no_data")
        self.assertEqual(dscr_row["actual"], "NO_DATA")
        self.assertEqual(report["data_sources"].get("dscr"), "NO_DATA")

    def test_compliance_apr_range_metric_ok_with_custom_guardrails(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(
            loans,
            payments,
            guardrails={"apr_pct_min": 30.0, "apr_pct_max": 40.0},
        )

        apr_row = next(row for row in report["metrics"] if row["metric"] == "apr_pct_ann")
        self.assertEqual(apr_row["status"], "ok")
        self.assertEqual(apr_row["target"], "30.0-40.0")
        self.assertEqual(apr_row["variance"], 0.0)

    def test_compliance_apr_range_metric_breach_below_min(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(
            loans,
            payments,
            guardrails={"apr_pct_min": 40.0, "apr_pct_max": 60.0},
        )

        apr_row = next(row for row in report["metrics"] if row["metric"] == "apr_pct_ann")
        self.assertEqual(apr_row["status"], "breach")
        self.assertLess(apr_row["variance"], 0)

    def test_compliance_dscr_metric_ok_when_inputs_present(self):
        loans = self._sample_loans().copy()
        payments = self._sample_payments()
        loans["net_operating_income"] = [300, 450, 360, 240, 210, 270]
        loans["debt_service"] = [200, 300, 240, 160, 140, 180]

        report = build_compliance_dashboard(
            loans,
            payments,
            guardrails={"dscr": 1.4, "apr_pct_min": 30.0, "apr_pct_max": 40.0},
        )

        dscr_row = next(row for row in report["metrics"] if row["metric"] == "dscr")
        self.assertEqual(dscr_row["status"], "ok")
        self.assertEqual(dscr_row["actual"], 1.5)
        self.assertEqual(dscr_row["target"], 1.4)

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

    def test_compliance_numeric_regression_par_and_concentration(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(loans, payments)
        by_metric = {row["metric"]: row for row in report["metrics"]}

        # Deterministic checks from sample fixture:
        # total balance = 6100
        # PAR30 balance = 1500 + 1200 + 700 = 3400 => 55.7%
        # PAR90 balance = 1200 + 700 = 1900 => 31.1%
        # Top-1 debtor balance = 2500 (P1) => 41.0%
        # Top-10 concentration includes all debtors in fixture => 100.0%
        self.assertEqual(by_metric["par30_pct"]["actual"], 55.7)
        self.assertEqual(by_metric["par90_pct"]["actual"], 31.1)
        self.assertEqual(by_metric["top1_concentration_pct"]["actual"], 41.0)
        self.assertEqual(by_metric["top10_concentration_pct"]["actual"], 100.0)

    def test_compliance_output_contract_shape(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(loans, payments)

        self.assertIn("generated_at", report)
        self.assertIn("summary", report)
        self.assertIn("metrics", report)
        self.assertIn("actuals", report)
        self.assertIn("data_sources", report)
        self.assertIn("variance_decomposition", report)
        self.assertIn("apr_pct_ann", report["variance_decomposition"])
        self.assertIn("dscr", report["variance_decomposition"])

        self.assertTrue(isinstance(report["metrics"], list))
        self.assertTrue(isinstance(report["actuals"], dict))
        self.assertTrue(isinstance(report["data_sources"], dict))

        required_metric_keys = {
            "metric",
            "actual",
            "target",
            "variance",
            "variance_pct",
            "status",
            "lower_is_better",
            "owner",
        }
        for row in report["metrics"]:
            self.assertTrue(required_metric_keys.issubset(set(row.keys())))

    def test_variance_decomposition_for_apr_and_dscr_when_missing(self):
        loans = self._sample_loans()
        payments = self._sample_payments()

        report = build_compliance_dashboard(loans, payments)
        decomp = report["variance_decomposition"]

        self.assertEqual(decomp["apr_pct_ann"]["driver"], "APR within policy corridor")
        self.assertEqual(decomp["dscr"]["driver"], "DSCR inputs unavailable")
        self.assertIsNone(decomp["dscr"]["magnitude"])

    def test_variance_decomposition_for_dscr_when_available(self):
        loans = self._sample_loans().copy()
        payments = self._sample_payments()
        loans["net_operating_income"] = [300, 450, 360, 240, 210, 270]
        loans["debt_service"] = [200, 300, 240, 160, 140, 180]

        report = build_compliance_dashboard(loans, payments, guardrails={"dscr": 1.4})
        decomp = report["variance_decomposition"]

        self.assertEqual(decomp["dscr"]["driver"], "Income coverage vs debt service")
        self.assertAlmostEqual(decomp["dscr"]["magnitude"], 0.1, places=2)

    def test_next_steps_plan_includes_apr_breach_action(self):
        compliance = {
            "metrics": [
                {
                    "metric": "apr_pct_ann",
                    "status": "breach",
                    "variance": 5.4,
                }
            ],
            "variance_decomposition": {
                "apr_pct_ann": {
                    "driver": "Pricing above target ceiling",
                    "explanation": "Weighted APR exceeds pricing corridor",
                }
            },
        }

        plan = build_next_steps_plan(forecast={}, compliance=compliance)
        apr_actions = [a for a in plan["actions"] if a["metric"] == "apr_pct_ann"]

        self.assertEqual(len(apr_actions), 1)
        self.assertIn("Pricing above target ceiling", apr_actions[0]["action"])

    def test_next_steps_plan_includes_dscr_no_data_action(self):
        compliance = {
            "metrics": [
                {
                    "metric": "dscr",
                    "status": "no_data",
                    "variance": None,
                }
            ],
            "variance_decomposition": {
                "dscr": {
                    "driver": "DSCR inputs unavailable",
                    "explanation": "NOI/debt_service fields missing",
                }
            },
        }

        plan = build_next_steps_plan(forecast={}, compliance=compliance)
        dscr_actions = [a for a in plan["actions"] if a["metric"] == "dscr"]

        self.assertEqual(len(dscr_actions), 1)
        self.assertEqual(dscr_actions[0]["source"], "compliance")
        self.assertIn("DSCR data unavailable", dscr_actions[0]["action"])
        self.assertIn("DSCR inputs unavailable", dscr_actions[0]["action"])

    def test_next_steps_plan_consolidates_duplicate_metric_actions(self):
        compliance = {
            "metrics": [
                {"metric": "apr_pct_ann", "status": "breach", "variance": 5.4},
                {"metric": "apr_pct_ann", "status": "breach", "variance": 2.1},
            ],
            "variance_decomposition": {
                "apr_pct_ann": {
                    "driver": "Pricing above target ceiling",
                    "explanation": "Weighted APR exceeds pricing corridor",
                }
            },
        }

        plan = build_next_steps_plan(forecast={}, compliance=compliance)
        apr_actions = [a for a in plan["actions"] if a["metric"] == "apr_pct_ann"]

        self.assertEqual(len(apr_actions), 1)
        self.assertEqual(apr_actions[0]["variance"], 5.4)
        self.assertIn("Pricing above target ceiling", apr_actions[0]["action"])

    def test_next_steps_plan_consolidates_semantic_duplicates_across_sources(self):
        compliance = {
            "metrics": [
                {"metric": "par30_pct", "status": "breach", "variance": 3.0},
            ],
            "variance_decomposition": {
                "par30_pct": {
                    "driver": "Rising delinquency in key segment",
                    "explanation": "PAR30 above threshold",
                }
            },
        }
        forecast = {
            "par30_forecast": [
                {"month": "M+1", "value": 20.0},
                {"month": "M+2", "value": 24.0},
            ]
        }

        plan = build_next_steps_plan(forecast=forecast, compliance=compliance)
        par30_like_actions = [
            a for a in plan["actions"] if a["metric"] in ("par30_pct", "par30")
        ]

        self.assertEqual(len(par30_like_actions), 1)
        self.assertEqual(par30_like_actions[0]["source"], "compliance+forecast")
        self.assertIn("Additional context", par30_like_actions[0]["action"])

    def test_next_steps_plan_supports_alias_metric_for_apr(self):
        compliance = {
            "metrics": [
                {"metric": "apr", "status": "breach", "variance": 4.2},
            ],
            "variance_decomposition": {
                "apr": {
                    "driver": "Pricing above target ceiling",
                    "explanation": "Alias metric received from upstream",
                }
            },
        }

        plan = build_next_steps_plan(forecast={}, compliance=compliance)
        apr_actions = [a for a in plan["actions"] if a["metric"] == "apr"]

        self.assertEqual(len(apr_actions), 1)
        self.assertEqual(apr_actions[0]["source"], "compliance")
        self.assertIn("Pricing above target ceiling", apr_actions[0]["action"])

    def test_next_steps_plan_consolidates_revenue_alias_across_sources(self):
        compliance = {
            "metrics": [
                {"metric": "revenue_usd", "status": "warning", "variance": -1200.0},
            ],
            "variance_decomposition": {
                "revenue_usd": {
                    "driver": "Pipeline conversion slowdown",
                    "explanation": "Monthly revenue below target",
                }
            },
        }
        forecast = {
            "revenue_forecast": [
                {"month": "M+1", "value": 10000.0},
                {"month": "M+2", "value": 8500.0},
            ]
        }

        plan = build_next_steps_plan(forecast=forecast, compliance=compliance)
        revenue_actions = [
            a for a in plan["actions"] if a["metric"] in ("revenue_usd", "revenue")
        ]

        self.assertEqual(len(revenue_actions), 1)
        self.assertEqual(revenue_actions[0]["source"], "compliance+forecast")
        self.assertIn("Additional context", revenue_actions[0]["action"])


if __name__ == "__main__":
    unittest.main()
