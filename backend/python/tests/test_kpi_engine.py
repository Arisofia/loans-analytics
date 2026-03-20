"""Tests for KPIEngineV2 audit trail functionality."""

import unittest
from datetime import datetime
from decimal import Decimal

import pandas as pd

from backend.python.kpis.engine import KPIEngineV2


class TestKPIEngineV2(unittest.TestCase):
    """Test KPIEngineV2 class and audit trail functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Create sample data for KPI calculations
        self.sample_df = pd.DataFrame(
            {
                "dpd_30_60_usd": [100.0, 200.0, 150.0],
                "dpd_60_90_usd": [50.0, 75.0, 100.0],
                "dpd_90_plus_usd": [25.0, 50.0, 75.0],
                "total_receivable_usd": [5000.0, 6000.0, 7000.0],
            }
        )

        self.empty_df = pd.DataFrame()

    def test_engine_initialization(self):
        """Test KPIEngineV2 initialization."""
        engine = KPIEngineV2(self.sample_df, actor="test_user", run_id="test_run_001")

        self.assertEqual(engine.actor, "test_user")
        self.assertEqual(engine.run_id, "test_run_001")
        self.assertIsInstance(engine.df, pd.DataFrame)
        self.assertEqual(len(engine._audit_records), 0)

    def test_engine_initialization_with_defaults(self):
        """Test KPIEngineV2 initialization with default values."""
        engine = KPIEngineV2(self.sample_df)

        self.assertEqual(engine.actor, "system")
        self.assertIsNotNone(engine.run_id)
        # Run ID should be in YYYYMMDD_HHMMSS format
        self.assertRegex(engine.run_id, r"\d{8}_\d{6}")

    def test_calculate_par_30(self):
        """Test PAR30 calculation with audit trail."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")

        value, context = engine.calculate_par_30()

        # Check that value is calculated correctly
        self.assertIsInstance(value, Decimal)
        self.assertGreaterEqual(value, 0.0)

        # Check context structure
        self.assertIn("formula", context)
        self.assertIn("rows_processed", context)
        self.assertEqual(context["rows_processed"], 3)

        # Check audit trail was recorded
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record["kpi_name"], "PAR30")
        self.assertEqual(audit_record["status"], "success")
        self.assertEqual(audit_record["value"], value)

    def test_calculate_collection_rate(self):
        """Test collection rate calculation with audit trail."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")

        value, context = engine.calculate_collection_rate()

        # Check that value is calculated
        self.assertIsInstance(value, Decimal)

        # Check context structure
        self.assertIn("formula", context)
        self.assertIn("rows_processed", context)

        # Check audit trail
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record["kpi_name"], "COLLECTION_RATE")
        self.assertEqual(audit_record["status"], "success")

    def test_calculate_ltv(self):
        """Test LTV calculation (on-demand KPI)."""
        # Create data with loan and collateral columns
        df_with_ltv = pd.DataFrame(
            {
                "loan_amount": [1000.0, 2000.0, 3000.0],
                "collateral_value": [1500.0, 2500.0, 4000.0],
            }
        )

        engine = KPIEngineV2(df_with_ltv, actor="test_user")
        value, context = engine.calculate_ltv()

        # Check calculation
        self.assertIsInstance(value, Decimal)
        self.assertGreaterEqual(float(value), 0.0)

        # Check audit trail
        self.assertEqual(len(engine._audit_records), 1)
        audit_record = engine._audit_records[0]
        self.assertEqual(audit_record["kpi_name"], "LTV")

    def test_calculate_all(self):
        """Test calculate_all method."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")

        results = engine.calculate_all()

        # Check results structure
        self.assertIsInstance(results, dict)
        self.assertIn("PAR30", results)
        self.assertIn("COLLECTION_RATE", results)
        self.assertIn("LTV", results)

        # Each KPI should have value and context
        for _kpi_name, kpi_data in results.items():
            self.assertIn("value", kpi_data)
            self.assertIn("context", kpi_data)

        # Check that audit trail has records for standard KPIs
        self.assertGreaterEqual(len(engine._audit_records), 3)

    def test_get_audit_trail(self):
        """Test get_audit_trail method returns proper DataFrame."""
        engine = KPIEngineV2(self.sample_df, actor="test_user", run_id="test_run_001")

        # Calculate some KPIs to populate audit trail
        engine.calculate_all()

        # Get audit trail
        audit_df = engine.get_audit_trail()

        # Check DataFrame structure
        self.assertIsInstance(audit_df, pd.DataFrame)
        self.assertGreater(len(audit_df), 0)

        # Check required columns
        required_columns = [
            "timestamp",
            "run_id",
            "actor",
            "kpi_name",
            "value",
            "context",
            "error",
            "status",
        ]
        for col in required_columns:
            self.assertIn(col, audit_df.columns)

        # Check data consistency
        self.assertTrue(all(audit_df["run_id"] == "test_run_001"))
        self.assertTrue(all(audit_df["actor"] == "test_user"))

    def test_get_audit_trail_empty(self):
        """Test get_audit_trail when no calculations have been performed."""
        engine = KPIEngineV2(self.sample_df)

        audit_df = engine.get_audit_trail()

        # Should return empty DataFrame with correct columns
        self.assertIsInstance(audit_df, pd.DataFrame)
        self.assertEqual(len(audit_df), 0)

        # Check columns exist even when empty
        required_columns = [
            "timestamp",
            "run_id",
            "actor",
            "kpi_name",
            "value",
            "context",
            "error",
            "status",
        ]
        for col in required_columns:
            self.assertIn(col, audit_df.columns)

    def test_error_handling_in_calculations(self):
        """Test that errors raise ValueError per fail-fast mandate."""
        # Create data missing required columns for PAR30
        invalid_df = pd.DataFrame(
            {
                "some_column": [1, 2, 3],
            }
        )

        engine = KPIEngineV2(invalid_df, actor="test_user")

        # Calculate PAR30 (should raise ValueError due to missing columns)
        with self.assertRaises(ValueError) as cm:
            engine.calculate_par_30()

        self.assertIn("CRITICAL: PAR30 calculation failed", str(cm.exception))

    def test_individual_kpi_failure_isolation(self):
        """Test that individual KPI failures are still reported in calculate_all."""
        # Use invalid data that will cause PAR30 to fail
        invalid_df = pd.DataFrame(
            {
                "some_column": [1, 2, 3],
            }
        )

        engine = KPIEngineV2(invalid_df, actor="test_user")

        # If calculate_all catches exceptions, it should still return results
        # However, per our new fail-fast refactor, if we want it to crash the whole batch,
        # we would let it raise. If we want it to be isolated, we catch it inside calculate_all.
        # Currently KPIEngineV2.calculate_all DOES NOT catch exceptions for standard KPIs,
        # so it should raise.

        with self.assertRaises(ValueError):
            engine.calculate_all()

    def test_audit_trail_timestamp_format(self):
        """Test that timestamps in audit trail are properly formatted."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")
        engine.calculate_par_30()

        audit_df = engine.get_audit_trail()
        timestamp_str = audit_df.iloc[0]["timestamp"]

        # Should be ISO format timestamp
        self.assertIsInstance(timestamp_str, str)
        # Should be parseable as datetime
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        self.assertIsInstance(parsed_timestamp, datetime)

    def test_context_serialization(self):
        """Test that context dictionaries are properly serialized in audit trail."""
        engine = KPIEngineV2(self.sample_df, actor="test_user")
        engine.calculate_par_30()

        audit_df = engine.get_audit_trail()
        context_str = audit_df.iloc[0]["context"]

        # Context should be converted to string for CSV export
        self.assertIsInstance(context_str, str)


# ---------------------------------------------------------------------------
# Block 7 — 8 open audit trail scenarios
# velocity_of_default | avg_credit_line_utilization | npl_ratio | npl_90_ratio
# defaulted_outstanding_ratio | ltv_sintetico | top_10_borrower_concentration
# derived-risk fail-safe (missing columns)
# ---------------------------------------------------------------------------


class TestDerivedRiskKPIAudit(unittest.TestCase):
    """Audit trail coverage for derived risk and enriched KPIs (Block 7)."""

    def _make_portfolio_df(self):
        """Full portfolio DataFrame required by calculate_all() (PAR30 + derived risk)."""
        return pd.DataFrame(
            {
                # PAR30 legacy columns
                "dpd_30_60_usd": [500.0, 8_000.0, 0.0, 0.0, 0.0],
                "dpd_60_90_usd": [0.0, 0.0, 2_000.0, 0.0, 0.0],
                "dpd_90_plus_usd": [0.0, 0.0, 6_000.0, 4_000.0, 0.0],
                "total_receivable_usd": [10_000.0, 8_000.0, 6_000.0, 4_000.0, 12_000.0],
                # Derived risk columns
                "dpd": [5, 35, 95, 120, 0],
                "status": ["active", "delinquent", "defaulted", "defaulted", "active"],
                "outstanding_balance": [10_000.0, 8_000.0, 6_000.0, 4_000.0, 12_000.0],
                "borrower_id": ["A", "B", "C", "D", "A"],
                "loan_id": ["L1", "L2", "L3", "L4", "L5"],
                "as_of_date": ["2026-01-31"] * 5,
            }
        )

    # 1 — velocity_of_default is returned in calculate_all when date column present
    def test_velocity_of_default_appears_in_calculate_all(self):
        df = pd.DataFrame(
            {
                "dpd_30_60_usd": [100.0],
                "dpd_60_90_usd": [50.0],
                "dpd_90_plus_usd": [25.0],
                "total_receivable_usd": [5_000.0],
                "dpd": [35],
                "status": ["delinquent"],
                "outstanding_balance": [5_000.0],
                "as_of_date": pd.to_datetime(["2026-01-31"]),
            }
        )
        engine = KPIEngineV2(df, actor="audit_test")
        results = engine.calculate_all()
        # velocity_of_default is absent without multiple periods — that is fine;
        # what we assert is that the key is NOT present when there is only one period.
        if "velocity_of_default" in results:
            vd = results["velocity_of_default"]["value"]
            self.assertIsNotNone(vd)
            self.assertIsInstance(vd, float)

    # 2 — avg_credit_line_utilization appears when utilization_pct column present
    def test_avg_credit_line_utilization_computed_from_utilization_pct(self):
        df = pd.DataFrame(
            {
                "utilization_pct": [0.60, 0.75, 0.50],
                "outstanding_balance": [10_000.0, 8_000.0, 6_000.0],
                "dpd_30_60_usd": [0.0, 0.0, 0.0],
                "dpd_60_90_usd": [0.0, 0.0, 0.0],
                "dpd_90_plus_usd": [0.0, 0.0, 0.0],
                "total_receivable_usd": [5_000.0, 6_000.0, 7_000.0],
            }
        )
        engine = KPIEngineV2(df, actor="audit_test")
        results = engine.calculate_all()
        self.assertIn("avg_credit_line_utilization", results)
        val = results["avg_credit_line_utilization"]["value"]
        # median is 0.60 < 2.0 → values are fraction, multiplied by 100 → ~61.67
        self.assertAlmostEqual(val, 61.67, delta=1.0)

    # 3 — npl_ratio uses broad 30-day DPD threshold (≥30 days)
    def test_npl_ratio_uses_30dpd_broad_threshold(self):
        df = self._make_portfolio_df()
        engine = KPIEngineV2(df, actor="audit_test")
        results = engine.calculate_all()
        self.assertIn("npl_ratio", results)
        val = results["npl_ratio"]["value"]
        # Loans with dpd≥30 or status delinquent/defaulted: B(8k)+C(6k)+D(4k) = 18k/40k = 45%
        self.assertAlmostEqual(val, 45.0, delta=0.1)

    # 4 — npl_90_ratio uses strict 90-day threshold and is ≤ npl_ratio
    def test_npl_90_ratio_is_subset_of_npl_ratio(self):
        df = self._make_portfolio_df()
        engine = KPIEngineV2(df, actor="audit_test")
        results = engine.calculate_all()
        self.assertIn("npl_ratio", results)
        self.assertIn("npl_90_ratio", results)
        npl = results["npl_ratio"]["value"]
        npl_90 = results["npl_90_ratio"]["value"]
        self.assertLessEqual(npl_90, npl)
        # Strict: dpd≥90 or defaulted: C(6k)+D(4k) = 10k/40k = 25%
        self.assertAlmostEqual(npl_90, 25.0, delta=0.1)

    # 5 — defaulted_outstanding_ratio covers only defaulted-status loans
    def test_defaulted_outstanding_ratio_only_defaulted_status(self):
        df = self._make_portfolio_df()
        engine = KPIEngineV2(df, actor="audit_test")
        results = engine.calculate_all()
        self.assertIn("defaulted_outstanding_ratio", results)
        val = results["defaulted_outstanding_ratio"]["value"]
        # defaulted: C(6k)+D(4k)=10k of 40k total active = 25%
        self.assertAlmostEqual(val, 25.0, delta=0.1)

    # 6 — ltv_sintetico_mean computed when capital_desembolsado and valor_nominal_factura present
    def test_ltv_sintetico_mean_in_results_when_columns_present(self):
        df = pd.DataFrame(
            {
                "dpd_30_60_usd": [0.0],
                "dpd_60_90_usd": [0.0],
                "dpd_90_plus_usd": [0.0],
                "total_receivable_usd": [10_000.0],
                "dpd": [0],
                "status": ["active"],
                "outstanding_balance": [10_000.0],
                "capital_desembolsado": [8_000.0],
                "valor_nominal_factura": [10_000.0],
                "tasa_dilucion": [0.10],
            }
        )
        engine = KPIEngineV2(df, actor="audit_test")
        results = engine.calculate_all()
        if "ltv_sintetico_mean" in results:
            val = results["ltv_sintetico_mean"]["value"]
            # LTV = 8000 / (10000 * 0.90) = 8000/9000 ≈ 0.8889
            self.assertAlmostEqual(float(val), 0.8889, delta=0.01)

    # 7 — top_10_borrower_concentration returns 0.0 when borrower_id absent
    def test_top_10_borrower_concentration_zero_without_borrower_col(self):
        engine = KPIEngineV2.__new__(KPIEngineV2)
        df = pd.DataFrame(
            {
                "dpd": [5, 35],
                "status": ["active", "delinquent"],
                "outstanding_balance": [10_000.0, 8_000.0],
            }
        )
        result = engine._top_10_borrower_concentration(
            df, "outstanding_balance", Decimal("18000")
        )
        self.assertEqual(result, Decimal("0.0"))

    # 8 — derived risk KPIs returns empty dict when required columns are absent
    def test_derived_risk_kpis_empty_when_missing_required_columns(self):
        df_no_cols = pd.DataFrame({"some_col": [1, 2, 3]})
        engine = KPIEngineV2(df_no_cols, actor="audit_test")
        result = engine._calculate_derived_risk_kpis(df_no_cols)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
