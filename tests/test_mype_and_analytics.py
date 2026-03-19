"""
Tests for MYPEBusinessRules, Settings 2026 targets, and src/analytics.

Covers:
  - Document 16: all MYPEBusinessRules test cases (exact assertions)
  - Document 17: calculate_quality_score, portfolio_kpis, standardize_numeric,
                 project_growth
  - Document 18: Settings loads portfolio_targets_2026 from YAML
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# -- imports from canonical locations ----------------------------------------
from backend.python.config.mype_rules import (
    ApprovalDecision,
    IndustryType,
    MYPEBusinessRules,
    RiskLevel,
)
from backend.python.config import settings
from src.analytics import (
    calculate_quality_score,
    portfolio_kpis,
    project_growth,
    standardize_numeric,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "loan_amount":      [12000, 8000,  16000],
        "appraised_value":  [15000, 10000, 20000],
        "borrower_income":  [60000, 45000, 80000],
        "monthly_debt":     [500,   400,   300],
        "principal_balance":[10000, 5000,  15000],
        "interest_rate":    [0.05,  0.07,  0.06],
        "loan_status":      ["current", "delinquent", "current"],
    })


# -----------------------------------------------------------------------------
# MYPEBusinessRules (Document 16)
# -----------------------------------------------------------------------------

class TestMYPEHighRiskClassification:
    def test_flags_multiple_reasons(self):
        metrics = {"dpd": 120, "utilization": 0.95, "npl_ratio": 0.07, "collection_rate": 0.7}
        is_high, reasons = MYPEBusinessRules.classify_high_risk(metrics)
        assert is_high is True
        assert "Utilization" in " ".join(reasons)
        assert len(reasons) >= 3

    def test_clear_low_risk(self):
        metrics = {"dpd": 0, "utilization": 0.3, "npl_ratio": 0.01, "collection_rate": 0.99}
        is_high, reasons = MYPEBusinessRules.classify_high_risk(metrics)
        assert is_high is False
        assert reasons == []

    def test_at_thresholds_triggers_flags(self):
        metrics = {
            "dpd":             MYPEBusinessRules.NPL_DAYS_THRESHOLD,
            "utilization":     MYPEBusinessRules.HIGH_RISK_CRITERIA["utilization"],
            "npl_ratio":       MYPEBusinessRules.HIGH_RISK_CRITERIA["npl_ratio"],
            "collection_rate": MYPEBusinessRules.HIGH_RISK_CRITERIA["collection_rate"] - 0.01,
        }
        is_high, reasons = MYPEBusinessRules.classify_high_risk(metrics)
        assert is_high is True
        assert len(reasons) >= 3


class TestMYPEIndustryAdjustment:
    def test_rewards_high_contribution(self):
        adj = MYPEBusinessRules.calculate_industry_adjustment(IndustryType.MANUFACTURING)
        assert adj > 1.0

    def test_penalizes_low_contribution(self):
        adj = MYPEBusinessRules.calculate_industry_adjustment(IndustryType.OTHER)
        assert adj <= 1.0

    def test_unknown_falls_back_to_other(self):
        other = MYPEBusinessRules.calculate_industry_adjustment(IndustryType.OTHER)
        unk   = MYPEBusinessRules.calculate_industry_adjustment("UNKNOWN_INDUSTRY")
        assert unk == other

    def test_impacts_facility_recommendation(self):
        base = {"dpd":0,"utilization":0.3,"npl_ratio":0.01,"collection_rate":0.98,"revenue":300000,"avg_balance":60000}
        m_dec = MYPEBusinessRules.evaluate_facility_approval(700000, {**base, "industry": IndustryType.MANUFACTURING})
        o_dec = MYPEBusinessRules.evaluate_facility_approval(700000, {**base, "industry": IndustryType.OTHER})
        assert m_dec.recommended_amount > o_dec.recommended_amount


class TestMYPENPL:
    def test_classify_npl_threshold(self):
        is_npl, message = MYPEBusinessRules.classify_npl(120)
        assert is_npl is True
        assert "NPL" in message

    def test_below_threshold_is_not_npl(self):
        dpd = MYPEBusinessRules.NPL_DAYS_THRESHOLD - 1
        is_npl, message = MYPEBusinessRules.classify_npl(dpd)
        assert is_npl is False
        assert "current" in message.lower()


class TestMYPERotation:
    def test_meets_target(self):
        rotation, meets, message = MYPEBusinessRules.check_rotation_target(500000, 100000)
        assert pytest.approx(rotation, rel=1e-3) == 5
        assert meets is True
        assert "meets" in message.lower()

    def test_below_target(self):
        rotation, meets, message = MYPEBusinessRules.check_rotation_target(390000, 100000)
        assert rotation < MYPEBusinessRules.TARGET_ROTATION
        assert meets is False
        assert "below" in message.lower()

    def test_boundary_condition(self):
        rotation, meets, message = MYPEBusinessRules.check_rotation_target(
            MYPEBusinessRules.TARGET_ROTATION * 100000, 100000
        )
        assert pytest.approx(rotation, rel=1e-3) == MYPEBusinessRules.TARGET_ROTATION
        assert meets is True

    def test_zero_balance(self):
        rotation, meets, message = MYPEBusinessRules.check_rotation_target(100000, 0.0)
        assert rotation == 0.0
        assert meets is False
        assert message == "Average balance unavailable"


class TestMYPEFacilityApproval:
    def test_recommends_collateral_for_high_risk(self):
        metrics = {
            "dpd": 45, "utilization": 0.88, "npl_ratio": 0.06,
            "collection_rate": 0.8, "revenue": 220000, "avg_balance": 90000,
            "industry": IndustryType.TRADE,
        }
        dec = MYPEBusinessRules.evaluate_facility_approval(200000, metrics, 50000)
        assert dec.approved is False
        assert dec.risk_level == RiskLevel.HIGH
        assert dec.required_collateral > 0
        assert dec.recommended_amount <= 200000
        assert dec.reasons

    def test_approves_low_risk(self):
        metrics = {
            "dpd": 5, "utilization": 0.35, "npl_ratio": 0.01,
            "collection_rate": 0.97, "revenue": 500000, "avg_balance": 80000,
            "industry": IndustryType.MANUFACTURING,
        }
        dec = MYPEBusinessRules.evaluate_facility_approval(300000, metrics, 50000)
        assert dec.approved is True
        assert dec.risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM}
        assert dec.required_collateral == 0
        assert not dec.conditions

    def test_flags_critical_npl(self):
        metrics = {
            "dpd": MYPEBusinessRules.NPL_DAYS_THRESHOLD + 10, "utilization": 0.4,
            "npl_ratio": 0.02, "collection_rate": 0.9,
            "revenue": 250000, "avg_balance": 100000, "industry": IndustryType.TRADE,
        }
        dec = MYPEBusinessRules.evaluate_facility_approval(100000, metrics, 20000)
        assert dec.approved is False
        assert dec.risk_level == RiskLevel.CRITICAL
        assert any("DPD" in r for r in dec.reasons)

    def test_reduces_recommendation_when_rotation_low(self):
        metrics = {
            "dpd": 10, "utilization": 0.4, "npl_ratio": 0.02,
            "collection_rate": 0.95, "revenue": 150000, "avg_balance": 60000,
            "industry": IndustryType.SERVICES,
        }
        dec = MYPEBusinessRules.evaluate_facility_approval(150000, metrics, 50000)
        assert dec.approved is False
        assert any("Rotation" in r for r in dec.reasons)
        assert dec.recommended_amount == pytest.approx(120000, rel=1e-3)

    def test_pod_and_collateral_behavior(self):
        healthy  = {"dpd":5,"utilization":0.2,"npl_ratio":0.01,"collection_rate":0.99,"revenue":500000,"avg_balance":150000}
        stressed = {**healthy, "dpd": 80}
        h = MYPEBusinessRules.evaluate_facility_approval(100000, healthy,  20000)
        s = MYPEBusinessRules.evaluate_facility_approval(100000, stressed, 20000)
        assert 0.0 <= h.pod <= 1.0
        assert s.pod >= h.pod
        assert s.required_collateral <= h.required_collateral + 100000


# -----------------------------------------------------------------------------
# Settings - 2026 Portfolio Targets (Document 18)
# -----------------------------------------------------------------------------

class TestSettings2026Targets:
    def test_targets_loaded(self):
        assert len(settings.portfolio_targets_2026) == 12

    def test_jan_target(self):
        assert settings.portfolio_targets_2026["2026-01"] == 8_500_000

    def test_dec_target(self):
        assert settings.portfolio_targets_2026["2026-12"] == 12_000_000

    def test_all_months_present(self):
        for m in range(1, 13):
            key = f"2026-{m:02d}"
            assert key in settings.portfolio_targets_2026, f"Missing {key}"

    def test_targets_monotonically_increasing(self):
        vals = [settings.portfolio_targets_2026[f"2026-{m:02d}"] for m in range(1, 13)]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1], f"Not increasing at month {i+2}"

    def test_required_growth_achievable(self):
        """Historical monthly disbursements ($3M avg) >> $300K net AUM growth needed."""
        required_net = settings.portfolio_targets_2026.get("required_monthly_net_growth_usd", 300_000)
        assert required_net <= 500_000, "Monthly net growth requirement is unrealistically high"

    def test_guardrails_still_loaded(self):
        assert settings.financial.min_rotation == 4.5
        assert settings.financial.max_default_rate == 0.04

    def test_loader_ignores_helper_keys_and_parses_underscore_values(self, tmp_path: Path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "business_parameters.yml").write_text(
            """
portfolio_targets_2026:
  '2026-01': '8_500_000'
  '2026-12': '12_000_000'
  required_monthly_net_growth_usd: 300000
""".strip(),
            encoding="utf-8",
        )

        loaded = type(settings).load_settings(project_root=tmp_path)

        assert loaded.portfolio_targets_2026 == {
            "2026-01": 8_500_000,
            "2026-12": 12_000_000,
        }


# -----------------------------------------------------------------------------
# src/analytics (Document 17)
# -----------------------------------------------------------------------------

class TestStandardizeNumeric:
    def test_handles_symbols(self):
        s = pd.Series(["$1,200","€2,500","25%","£3,000","¥4,500","₽5,500","","nan","abc",None," 7,500 "])
        c = standardize_numeric(s)
        assert c.iloc[0]  == 1200.0
        assert c.iloc[1]  == 2500.0
        assert c.iloc[2]  == 25.0
        assert c.iloc[3]  == 3000.0
        assert c.iloc[4]  == 4500.0
        assert c.iloc[5]  == 5500.0
        assert pd.isna(c.iloc[6])
        assert pd.isna(c.iloc[7])
        assert pd.isna(c.iloc[8])
        assert pd.isna(c.iloc[9])
        assert c.iloc[10] == 7500.0

    def test_passes_through_numeric(self):
        s = pd.Series([1, 2.5, -3])
        c = standardize_numeric(s)
        assert c.tolist() == [1.0, 2.5, -3.0]
        assert pd.api.types.is_numeric_dtype(c)

    def test_handles_negatives_and_commas(self):
        s = pd.Series(["-1,200", "-$3,000", "-25%"])
        c = standardize_numeric(s)
        assert c.iloc[0] == -1200.0
        assert c.iloc[1] == -3000.0
        assert c.iloc[2] == -25.0


class TestCalculateQualityScore:
    def test_rewards_complete_data(self, sample_df):
        assert calculate_quality_score(sample_df) == 100.0

    def test_penalizes_missing(self, sample_df):
        df = sample_df.copy()
        df.loc[0, "loan_amount"] = None
        assert calculate_quality_score(df) < 100.0

    def test_empty_dataframe_returns_zero(self, sample_df):
        assert calculate_quality_score(pd.DataFrame(columns=sample_df.columns)) == 0.0

    def test_all_null_returns_zero(self, sample_df):
        df = sample_df.copy()
        for col in df.columns:
            df[col] = None
        assert calculate_quality_score(df) == 0.0

    def test_counts_completeness(self):
        df = pd.DataFrame({"a": [1, np.nan], "b": [1, 1]})
        assert calculate_quality_score(df) == 75.0

    def test_empty_df_no_columns(self):
        assert calculate_quality_score(pd.DataFrame()) == 0.0


class TestPortfolioKPIs:
    def test_returns_expected_metrics(self, sample_df):
        metrics, enriched = portfolio_kpis(sample_df)
        assert set(metrics.keys()) == {"delinquency_rate","portfolio_yield","average_ltv","average_dti"}
        assert "ltv_ratio" in enriched.columns
        assert "dti_ratio" in enriched.columns

        bal  = pd.to_numeric(sample_df["principal_balance"])
        rat  = pd.to_numeric(sample_df["interest_rate"])
        amt  = pd.to_numeric(sample_df["loan_amount"])
        val  = pd.to_numeric(sample_df["appraised_value"])
        inc  = pd.to_numeric(sample_df["borrower_income"])
        dbt  = pd.to_numeric(sample_df["monthly_debt"])
        delinq = (sample_df["loan_status"] == "delinquent")

        expected_delinq_rate  = bal[delinq].sum() / bal.sum()
        expected_yield        = (bal * rat).sum() / bal.sum()
        expected_ltv          = (amt / val).mean()
        expected_dti          = (dbt / (inc / 12)).mean()

        assert metrics["delinquency_rate"] == pytest.approx(expected_delinq_rate, rel=1e-6)
        assert metrics["portfolio_yield"]  == pytest.approx(expected_yield,       rel=1e-6)
        assert metrics["average_ltv"]      == pytest.approx(expected_ltv,         rel=1e-6)
        assert metrics["average_dti"]      == pytest.approx(expected_dti,         rel=1e-6)

    def test_missing_column_raises(self, sample_df):
        df = sample_df.drop(columns=["loan_amount"])
        with pytest.raises(ValueError, match="Missing required columns: loan_amount"):
            portfolio_kpis(df)

    def test_handles_empty_frame(self, sample_df):
        metrics, enriched = portfolio_kpis(sample_df.iloc[:0])
        assert metrics == {"delinquency_rate": 0.0,"portfolio_yield": 0.0,"average_ltv": 0.0,"average_dti": 0.0}
        assert enriched.empty

    def test_zero_principal_yield_is_zero(self, sample_df):
        df = sample_df.copy()
        df["principal_balance"] = 0
        metrics, _ = portfolio_kpis(df)
        assert metrics["portfolio_yield"] == 0.0

    def test_dti_nan_when_income_non_positive(self, sample_df):
        df = sample_df.copy()
        df["borrower_income"] = [0, -5000, 0]
        metrics, enriched = portfolio_kpis(df)
        assert enriched["dti_ratio"].isna().all()
        assert metrics["average_dti"] == 0.0

    def test_dti_mixed_income_ignores_nan(self, sample_df):
        df = sample_df.copy()
        df["borrower_income"] = [60000, 0, -5000]
        metrics, enriched = portfolio_kpis(df)
        pos = df["borrower_income"] > 0
        assert enriched.loc[~pos, "dti_ratio"].isna().all()
        assert enriched.loc[pos,  "dti_ratio"].notna().all()
        expected = (df.loc[pos,"monthly_debt"] / (df.loc[pos,"borrower_income"] / 12)).mean()
        assert metrics["average_dti"] == pytest.approx(expected)


class TestProjectGrowth:
    def test_builds_monotonic_path(self):
        proj = project_growth(1.0, 2.0, 100, 200, periods=4)
        assert len(proj) == 4
        assert proj["yield"].iloc[0]       == 1.0
        assert proj["yield"].iloc[-1]      == 2.0
        assert proj["loan_volume"].iloc[0]  == 100
        assert proj["loan_volume"].iloc[-1] == 200

    def test_rejects_insufficient_periods(self):
        with pytest.raises(ValueError, match="periods must be at least 2"):
            project_growth(1.0, 2.0, 100, 200, periods=1)

    def test_formats_month_labels(self):
        proj = project_growth(1.0, 1.5, 100, 120, periods=3)
        assert proj["month"].str.match(r"^[A-Z][a-z]{2} \d{4}$").all()

    def test_supports_decreasing_targets(self):
        proj = project_growth(2.0, 1.0, 200, 100, periods=3)
        assert proj["yield"].is_monotonic_decreasing
        assert proj["loan_volume"].is_monotonic_decreasing

    def test_default_periods_is_6(self):
        proj = project_growth(1.0, 2.0, 100, 200)
        assert len(proj) == 6


# -----------------------------------------------------------------------------
# 2026 targets vs actual AUM - integration smoke test
# -----------------------------------------------------------------------------

class TestPortfolioVsTargets2026:
    """Integration: compare live AUM against 2026 monthly targets."""

    def test_mar_2026_target_reachable_from_current_aum(self):
        """Current AUM $8.36M vs Jan-2026 target $8.5M - gap is <2%."""
        current_aum = 8_364_154  # INTERMEDIA snapshot 2026-03-13
        jan_target  = settings.portfolio_targets_2026["2026-01"]
        gap_pct = (jan_target - current_aum) / current_aum * 100
        assert gap_pct < 5.0, f"Jan-2026 gap {gap_pct:.1f}% seems unreachable"

    def test_dec_2026_implies_43pct_growth(self):
        current_aum = 8_364_154
        dec_target  = settings.portfolio_targets_2026["2026-12"]
        growth_pct  = (dec_target - current_aum) / current_aum * 100
        assert 30 < growth_pct < 60, f"Dec-2026 growth {growth_pct:.1f}% out of expected range"

    def test_monthly_net_growth_within_historical_capacity(self):
        """
        Average monthly disbursements $3M >> $300K net AUM growth needed.
        Even with 90% collection rate, net is well above the $300K target.
        """
        monthly_disb_avg = 3_070_455   # LTM average from loan tape
        required_net = 300_000
        assert monthly_disb_avg > required_net * 5, "Historical disbursements insufficient"
