"""Tests for the KPIEngineV2 deprecated compatibility shim.

The canonical KPI authority is run_metric_engine() from backend.src.kpi_engine.engine.
These tests verify:
  1.  KPIEngineV2 emits a DeprecationWarning on instantiation.
  2.  calculate_all() / calculate() delegate to run_metric_engine() and return
      a well-structured dict.
  3.  get_audit_trail() returns an empty DataFrame with the expected columns
      (the shim no longer tracks per-call audit records).
  4.  NPL / PAR semantics are correct end-to-end through the shim.
"""
from __future__ import annotations

import decimal
import unittest
import warnings
from decimal import ROUND_HALF_UP, getcontext

import pandas as pd

# Ensure the ROUND_HALF_UP context is active before any SSOT import in this
# module's transitive dependency chain (ssot_asset_quality.py asserts it).
# This mirrors the conftest.py module-level setup and is intentional defensive
# duplication: if this test file is ever run in a fresh interpreter without
# the conftest module-level initialization (e.g. via `python -m unittest`),
# the assertion will not fire unexpectedly.
getcontext().rounding = ROUND_HALF_UP

from backend.loans_analytics.kpis.engine import KPIEngineV2  # noqa: E402


# ---------------------------------------------------------------------------
# Shared test fixture factory
# ---------------------------------------------------------------------------

def _make_portfolio_df() -> pd.DataFrame:
    """Minimal portfolio DataFrame accepted by run_metric_engine.

    Provides the columns that risk functions access directly:
      - outstanding_principal  (used by compute_par30/60/90)
      - days_past_due          (used by compute_par30/60/90, compute_npl_ratio)
      - loan_status            (used by _status_series → _defaulted_mask)
    """
    return pd.DataFrame(
        {
            "outstanding_principal": [10000.0, 8000.0, 6000.0, 4000.0, 12000.0],
            "days_past_due": [5, 35, 95, 120, 0],
            "loan_status": [
                "current",
                "delinquent",
                "defaulted",
                "defaulted",
                "current",
            ],
        }
    )


# ---------------------------------------------------------------------------
# TestKPIEngineV2 — shim interface contracts
# ---------------------------------------------------------------------------


class TestKPIEngineV2(unittest.TestCase):
    """Verify the public interface of the deprecated KPIEngineV2 shim."""

    def setUp(self) -> None:
        self.portfolio_df = _make_portfolio_df()
        self.empty_df = pd.DataFrame()

    # ── Construction ────────────────────────────────────────────────────────

    def test_engine_initialization_stores_attributes(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(
                self.portfolio_df, actor="test_user", run_id="test_run_001"
            )
        self.assertEqual(engine.actor, "test_user")
        self.assertEqual(engine.run_id, "test_run_001")
        self.assertIsInstance(engine.df, pd.DataFrame)

    def test_engine_initialization_default_actor(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df)
        self.assertEqual(engine.actor, "system")

    def test_engine_emits_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            KPIEngineV2(self.portfolio_df)
        self.assertTrue(
            any(issubclass(warning.category, DeprecationWarning) for warning in w),
            "Expected DeprecationWarning on KPIEngineV2 instantiation",
        )

    # ── calculate_all ───────────────────────────────────────────────────────

    def test_calculate_all_returns_dict(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        results = engine.calculate_all()
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)

    def test_calculate_all_entries_have_value_and_context(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        results = engine.calculate_all()
        for metric_id, entry in results.items():
            self.assertIn("value", entry, f"{metric_id} missing 'value'")
            self.assertIn("context", entry, f"{metric_id} missing 'context'")

    def test_calculate_all_includes_core_risk_metrics(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        results = engine.calculate_all()
        for expected_key in ("par30", "par60", "par90", "npl_ratio"):
            self.assertIn(expected_key, results, f"Missing expected metric: {expected_key}")

    def test_calculate_all_empty_portfolio_returns_dict(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.empty_df, actor="test_user")
        results = engine.calculate_all()
        self.assertIsInstance(results, dict)

    # ── calculate (legacy entrypoint) ───────────────────────────────────────

    def test_calculate_delegates_to_canonical_engine(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        result = engine.calculate(self.portfolio_df)
        self.assertIsInstance(result, dict)
        self.assertIn("npl_ratio", result)

    # ── get_audit_trail ─────────────────────────────────────────────────────

    def test_get_audit_trail_returns_dataframe(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        audit_df = engine.get_audit_trail()
        self.assertIsInstance(audit_df, pd.DataFrame)

    def test_get_audit_trail_has_required_columns(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        audit_df = engine.get_audit_trail()
        for col in ("kpi_name", "status", "value", "timestamp"):
            self.assertIn(col, audit_df.columns, f"Missing audit column: {col}")

    def test_get_audit_trail_is_empty_shim(self) -> None:
        """The shim returns an empty audit trail; full audit lives in run_metric_engine."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            engine = KPIEngineV2(self.portfolio_df, actor="test_user")
        engine.calculate_all()
        audit_df = engine.get_audit_trail()
        self.assertEqual(len(audit_df), 0)


# ---------------------------------------------------------------------------
# TestDerivedRiskKPIAudit — NPL / PAR doctrine through the shim
# ---------------------------------------------------------------------------


class TestDerivedRiskKPIAudit(unittest.TestCase):
    """End-to-end verification that risk KPI semantics are correct through the shim."""

    # NPL = 25 % of portfolio:
    #   index 2: dpd=95  (>=90) AND status=defaulted  → included
    #   index 3: dpd=120 (>=90) AND status=defaulted  → included
    #   balance: 6 000 + 4 000 = 10 000 / 40 000 total = 0.25
    _PORTFOLIO = {
        "outstanding_principal": [10000.0, 8000.0, 6000.0, 4000.0, 12000.0],
        "days_past_due": [5, 35, 95, 120, 0],
        "loan_status": [
            "current",
            "delinquent",
            "defaulted",
            "defaulted",
            "current",
        ],
    }

    def _make_engine(self, data: dict | None = None) -> KPIEngineV2:
        df = pd.DataFrame(data or self._PORTFOLIO)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return KPIEngineV2(df, actor="audit_test")

    # ── NPL doctrine ────────────────────────────────────────────────────────

    def test_npl_ratio_uses_strict_90dpd_threshold(self) -> None:
        """NPL must apply DPD >= 90 OR status=defaulted (Basel-II/III)."""
        results = self._make_engine().calculate_all()
        self.assertIn("npl_ratio", results)
        val = float(results["npl_ratio"]["value"])
        # 10 000 / 40 000 = 0.25
        self.assertAlmostEqual(val, 0.25, delta=0.01)

    def test_npl_ratio_is_zero_for_current_portfolio(self) -> None:
        """NPL must be zero when no loan has DPD >= 90 and none are defaulted."""
        data = {
            "outstanding_principal": [10000.0, 8000.0, 12000.0],
            "days_past_due": [0, 15, 45],
            "loan_status": ["current", "current", "delinquent"],
        }
        results = self._make_engine(data).calculate_all()
        self.assertIn("npl_ratio", results)
        self.assertEqual(float(results["npl_ratio"]["value"]), 0.0)

    # ── PAR doctrine ────────────────────────────────────────────────────────

    def test_par30_is_balance_weighted(self) -> None:
        """PAR30 must be (balance where DPD >= 30) / total_balance."""
        data = {
            "outstanding_principal": [10000.0, 5000.0, 15000.0],
            "days_past_due": [0, 35, 65],
            "loan_status": ["current", "delinquent", "delinquent"],
        }
        results = self._make_engine(data).calculate_all()
        self.assertIn("par30", results)
        val = float(results["par30"]["value"])
        # (5 000 + 15 000) / 30 000 = 0.6667
        self.assertAlmostEqual(val, 0.6667, delta=0.01)

    def test_par90_is_subset_of_par30(self) -> None:
        """PAR90 must be <= PAR30 for any portfolio."""
        results = self._make_engine().calculate_all()
        par30 = float(results["par30"]["value"])
        par90 = float(results["par90"]["value"])
        self.assertLessEqual(par90, par30)

    # ── Default rate ────────────────────────────────────────────────────────

    def test_default_rate_by_balance_uses_defaulted_status(self) -> None:
        """default_rate_by_balance counts only status=defaulted loans."""
        results = self._make_engine().calculate_all()
        self.assertIn("default_rate_by_balance", results)
        val = float(results["default_rate_by_balance"]["value"])
        # 6 000 + 4 000 = 10 000 / 40 000 = 0.25
        self.assertAlmostEqual(val, 0.25, delta=0.01)

    # ── Edge cases ──────────────────────────────────────────────────────────

    def test_calculate_all_with_empty_df_does_not_raise(self) -> None:
        """calculate_all must return a dict for an empty portfolio, not raise."""
        results = self._make_engine({"outstanding_principal": [], "days_past_due": [], "loan_status": []}).calculate_all()
        self.assertIsInstance(results, dict)


if __name__ == "__main__":
    unittest.main()
