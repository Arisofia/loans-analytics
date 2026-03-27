"""Tests for newly added KPI engine functions.

Covers:
- unit_economics: calculate_weighted_statistics, calculate_line_utilization
- risk: classify_dpd_buckets, segment_clients_by_exposure,
        compute_customer_dpd_stats, build_feature_engineering_pipeline
- portfolio_analytics: analyze_small_line_rotation,
        segment_portfolio_by_line_blocks, compute_rate_by_amount_tiers,
        compute_default_by_segment, compute_max_mora_by_segment,
        compute_churn_analysis, compute_pricing_recommendations,
        compute_income_and_revenue
"""
from __future__ import annotations

import pandas as pd
import pytest

from backend.src.kpi_engine.unit_economics import (
    calculate_line_utilization,
    calculate_weighted_statistics,
)
from backend.src.kpi_engine.risk import (
    classify_dpd_buckets,
    segment_clients_by_exposure,
    compute_customer_dpd_stats,
    build_feature_engineering_pipeline,
)
from backend.src.kpi_engine.portfolio_analytics import (
    analyze_small_line_rotation,
    compute_churn_analysis,
    compute_default_by_segment,
    compute_income_and_revenue,
    compute_max_mora_by_segment,
    compute_pricing_recommendations,
    compute_rate_by_amount_tiers,
    segment_portfolio_by_line_blocks,
)


# ── shared fixture ─────────────────────────────────────────────────────────────

@pytest.fixture()
def portfolio_df() -> pd.DataFrame:
    """10-row portfolio fixture covering all segments, dpd buckets, and amounts."""
    return pd.DataFrame(
        {
            "loan_id":              ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09", "L10"],
            "customer_id":          ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C01", "C03"],
            "segment":              ["Nimal", "Nimal", "Gob", "Gob", "OC", "OC", "Top", "Top", "Nimal", "Gob"],
            "loan_amount":          [5_000, 15_000, 30_000, 80_000, 120_000, 300_000, 600_000, 50_000, 8_000, 45_000],
            "outstanding_balance":  [4_500, 13_000, 27_000, 70_000, 100_000, 270_000, 550_000, 45_000, 7_200, 40_000],
            "line_amount":          [10_000, 20_000, 50_000, 100_000, 150_000, 400_000, 800_000, 75_000, 10_000, 60_000],
            "term_days":            [30, 60, 90, 45, 30, 120, 180, 25, 15, 30],
            "term_months":          [1, 2, 3, 1.5, 1, 4, 6, 0.8, 0.5, 1],
            "apr":                  [0.36, 0.28, 0.24, 0.20, 0.18, 0.15, 0.12, 0.22, 0.36, 0.24],
            "origination_fee_rate": [0.03, 0.025, 0.02, 0.02, 0.015, 0.01, 0.01, 0.02, 0.03, 0.02],
            "days_past_due":        [0, 0, 15, 45, 75, 95, 0, 0, 32, 0],
            "default_flag":         [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "origination_date":     [
                "2025-01-05", "2025-02-10", "2025-03-01", "2024-12-15",
                "2025-01-20", "2024-10-01", "2025-03-20", "2025-04-01",
                "2025-09-10", "2025-06-01",
            ],
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
# unit_economics — calculate_weighted_statistics
# ══════════════════════════════════════════════════════════════════════════════

class TestCalculateWeightedStatistics:
    def test_weighted_apr_by_balance(self, portfolio_df: pd.DataFrame) -> None:
        result = calculate_weighted_statistics(
            portfolio_df, metrics=["apr"], weight_col="outstanding_balance"
        )
        assert "apr" in result
        # Manual: (4500*.36 + 13000*.28 + ...) / sum(balances)
        total_w = portfolio_df["outstanding_balance"].sum()
        expected = (portfolio_df["apr"] * portfolio_df["outstanding_balance"]).sum() / total_w
        assert abs(result["apr"] - expected) < 1e-5

    def test_multiple_metrics(self, portfolio_df: pd.DataFrame) -> None:
        result = calculate_weighted_statistics(
            portfolio_df, metrics=["apr", "term_months"], weight_col="outstanding_balance"
        )
        assert set(result.keys()) == {"apr", "term_months"}
        assert result["apr"] > 0
        assert result["term_months"] > 0

    def test_missing_metric_returns_zero(self, portfolio_df: pd.DataFrame) -> None:
        result = calculate_weighted_statistics(
            portfolio_df, metrics=["nonexistent_col"], weight_col="outstanding_balance"
        )
        assert result["nonexistent_col"] == 0.0

    def test_empty_dataframe(self) -> None:
        result = calculate_weighted_statistics(pd.DataFrame(), metrics=["apr", "term_months"])
        assert result == {"apr": 0.0, "term_months": 0.0}

    def test_zero_weight_falls_back_to_mean(self, portfolio_df: pd.DataFrame) -> None:
        df = portfolio_df.copy()
        df["outstanding_balance"] = 0
        result = calculate_weighted_statistics(df, metrics=["apr"], weight_col="outstanding_balance")
        assert abs(result["apr"] - df["apr"].mean()) < 1e-5


# ══════════════════════════════════════════════════════════════════════════════
# unit_economics — calculate_line_utilization
# ══════════════════════════════════════════════════════════════════════════════

class TestCalculateLineUtilization:
    def test_utilization_computed_correctly(self, portfolio_df: pd.DataFrame) -> None:
        result = calculate_line_utilization(
            portfolio_df,
            credit_line_field="line_amount",
            loan_amount_field="outstanding_balance",
        )
        assert "line_utilization" in result.columns
        # L01: 4500/10000 = 0.45
        assert abs(float(result.loc[result["loan_id"] == "L01", "line_utilization"].iloc[0]) - 0.45) < 1e-4

    def test_utilization_capped_at_1(self) -> None:
        df = pd.DataFrame({"loan_id": ["X"], "line_amount": [100], "outstanding_balance": [150]})
        result = calculate_line_utilization(df, "line_amount", "outstanding_balance")
        assert float(result["line_utilization"].iloc[0]) == 1.0

    def test_zero_line_returns_zero(self) -> None:
        df = pd.DataFrame({"loan_id": ["X"], "line_amount": [0], "outstanding_balance": [500]})
        result = calculate_line_utilization(df, "line_amount", "outstanding_balance")
        assert float(result["line_utilization"].iloc[0]) == 0.0

    def test_missing_column_returns_zero_column(self, portfolio_df: pd.DataFrame) -> None:
        result = calculate_line_utilization(
            portfolio_df, credit_line_field="nonexistent_col", loan_amount_field="outstanding_balance"
        )
        assert "line_utilization" in result.columns
        assert (result["line_utilization"] == 0.0).all()


# ══════════════════════════════════════════════════════════════════════════════
# risk — classify_dpd_buckets
# ══════════════════════════════════════════════════════════════════════════════

class TestClassifyDpdBuckets:
    def test_bucket_labels(self, portfolio_df: pd.DataFrame) -> None:
        result = classify_dpd_buckets(portfolio_df)
        assert "dpd_bucket" in result.columns
        dpd_map = result.set_index("loan_id")["dpd_bucket"].to_dict()
        assert dpd_map["L01"] == "current"   # dpd=0
        assert dpd_map["L03"] == "1_30"      # dpd=15
        assert dpd_map["L04"] == "31_60"     # dpd=45
        assert dpd_map["L05"] == "61_90"     # dpd=75
        assert dpd_map["L06"] == "90_plus"   # dpd=95

    def test_missing_dpd_col_defaults_current(self, portfolio_df: pd.DataFrame) -> None:
        df = portfolio_df.drop(columns=["days_past_due"])
        result = classify_dpd_buckets(df)
        assert (result["dpd_bucket"] == "current").all()

    def test_custom_output_col(self, portfolio_df: pd.DataFrame) -> None:
        result = classify_dpd_buckets(portfolio_df, output_col="bucket")
        assert "bucket" in result.columns


# ══════════════════════════════════════════════════════════════════════════════
# risk — segment_clients_by_exposure
# ══════════════════════════════════════════════════════════════════════════════

class TestSegmentClientsByExposure:
    def test_tier_labels(self, portfolio_df: pd.DataFrame) -> None:
        result = segment_clients_by_exposure(portfolio_df, balance_col="outstanding_balance")
        assert "exposure_segment" in result.columns
        seg_map = result.set_index("loan_id")["exposure_segment"].to_dict()
        assert seg_map["L01"] == "Micro"    # 4500
        assert seg_map["L03"] == "Small"    # 27000
        assert seg_map["L04"] == "Medium"   # 70000
        assert seg_map["L05"] == "Large"    # 100000
        assert seg_map["L07"] == "Major"    # 550000

    def test_inactive_tier(self) -> None:
        df = pd.DataFrame({"outstanding_balance": [0.0]})
        result = segment_clients_by_exposure(df)
        assert result["exposure_segment"].iloc[0] == "Inactive"

    def test_missing_balance_col(self, portfolio_df: pd.DataFrame) -> None:
        df = portfolio_df.drop(columns=["outstanding_balance"])
        result = segment_clients_by_exposure(df)
        assert (result["exposure_segment"] == "Unknown").all()


# ══════════════════════════════════════════════════════════════════════════════
# risk — compute_customer_dpd_stats
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeCustomerDpdStats:
    def test_aggregation(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_customer_dpd_stats(portfolio_df)
        assert "dpd_mean" in result.columns
        assert "dpd_max" in result.columns
        assert "dpd_count" in result.columns
        # C01 has loans L01 (dpd=0) and L09 (dpd=32) → max=32, count=2
        c01 = result[result["customer_id"] == "C01"].iloc[0]
        assert int(c01["dpd_max"]) == 32
        assert int(c01["dpd_count"]) == 2

    def test_empty_returns_empty_df(self) -> None:
        result = compute_customer_dpd_stats(pd.DataFrame())
        assert result.empty

    def test_missing_dpd_col(self, portfolio_df: pd.DataFrame) -> None:
        df = portfolio_df.drop(columns=["days_past_due"])
        result = compute_customer_dpd_stats(df, dpd_col="days_past_due")
        # Should still return customers with dpd=0
        assert not result.empty
        assert (result["dpd_max"] == 0).all()


# ══════════════════════════════════════════════════════════════════════════════
# risk — build_feature_engineering_pipeline
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildFeatureEngineeringPipeline:
    def test_adds_dpd_bucket(self, portfolio_df: pd.DataFrame) -> None:
        result = build_feature_engineering_pipeline(portfolio_df)
        assert "dpd_bucket" in result.columns

    def test_adds_exposure_segment(self, portfolio_df: pd.DataFrame) -> None:
        result = build_feature_engineering_pipeline(portfolio_df)
        assert "exposure_segment" in result.columns

    def test_adds_zscore(self, portfolio_df: pd.DataFrame) -> None:
        result = build_feature_engineering_pipeline(portfolio_df)
        assert "apr_zscore" in result.columns
        assert "outstanding_balance_zscore" in result.columns

    def test_adds_line_utilization_zscore_when_line_present(self, portfolio_df: pd.DataFrame) -> None:
        result = build_feature_engineering_pipeline(portfolio_df)
        assert "line_utilization" in result.columns
        assert "line_utilization_zscore" in result.columns

    def test_missing_required_columns_returns_unchanged(self) -> None:
        df = pd.DataFrame({"loan_id": ["L1"], "whatever": [1]})
        result = build_feature_engineering_pipeline(df)
        assert list(result.columns) == ["loan_id", "whatever"]


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — analyze_small_line_rotation
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeSmallLineRotation:
    def test_filters_correctly(self, portfolio_df: pd.DataFrame) -> None:
        result = analyze_small_line_rotation(
            portfolio_df,
            line_threshold=100_000,
            rotation_days=30,
        )
        # Lines < 100K: L01(10K), L02(20K), L03(50K), L08(75K), L09(10K), L10(60K)
        # Of those, term_days <= 30: L01(30), L08(25), L09(15), L10(30)
        assert result["total_loans"] >= 1
        assert result["total_balance_usd"] > 0

    def test_empty_returns_zero(self) -> None:
        result = analyze_small_line_rotation(pd.DataFrame())
        assert result["total_clients"] == 0

    def test_criteria_included(self, portfolio_df: pd.DataFrame) -> None:
        result = analyze_small_line_rotation(portfolio_df, line_threshold=50_000, rotation_days=60)
        assert result["criteria"]["line_lt_usd"] == 50_000
        assert result["criteria"]["rotation_lte_days"] == 60


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — segment_portfolio_by_line_blocks
# ══════════════════════════════════════════════════════════════════════════════

class TestSegmentPortfolioByLineBlocks:
    def test_returns_blocks(self, portfolio_df: pd.DataFrame) -> None:
        blocks = segment_portfolio_by_line_blocks(portfolio_df, block_size=100_000)
        assert isinstance(blocks, list)
        assert len(blocks) > 0

    def test_block_labels_format(self, portfolio_df: pd.DataFrame) -> None:
        blocks = segment_portfolio_by_line_blocks(portfolio_df, block_size=100_000)
        labels = [b["block_label"] for b in blocks]
        # First block should be $0K–$100K
        assert "$0K–$100K" in labels

    def test_share_pct_sums_to_100(self, portfolio_df: pd.DataFrame) -> None:
        blocks = segment_portfolio_by_line_blocks(portfolio_df, block_size=100_000)
        total_share = sum(b["share_pct"] for b in blocks)
        assert abs(total_share - 100.0) < 0.01

    def test_sorted_by_line_min(self, portfolio_df: pd.DataFrame) -> None:
        blocks = segment_portfolio_by_line_blocks(portfolio_df, block_size=100_000)
        mins = [b["line_min_usd"] for b in blocks]
        assert mins == sorted(mins)

    def test_empty_returns_empty(self) -> None:
        assert segment_portfolio_by_line_blocks(pd.DataFrame()) == []


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — compute_rate_by_amount_tiers
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeRateByAmountTiers:
    def test_returns_list(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_rate_by_amount_tiers(portfolio_df)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_small_loan_tier_has_min_commission(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_rate_by_amount_tiers(portfolio_df)
        small_tier = next((r for r in result if r["tier"] == "<$10K"), None)
        assert small_tier is not None
        assert small_tier["min_commission_usd"] == 500.0

    def test_higher_rate_for_small_loans(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_rate_by_amount_tiers(portfolio_df)
        tiers_with_data = [r for r in result if r["loan_count"] > 0]
        # Small loan tiers should have higher rates than large
        rates = {r["tier"]: r["weighted_avg_rate_pct"] for r in tiers_with_data}
        if "<$10K" in rates and "$500K+" in rates:
            assert rates["<$10K"] > rates["$500K+"]

    def test_empty_returns_list(self) -> None:
        result = compute_rate_by_amount_tiers(pd.DataFrame())
        assert result == []


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — compute_default_by_segment
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeDefaultBySegment:
    def test_returns_all_segments(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_default_by_segment(portfolio_df)
        segments = {r["segment"] for r in result}
        assert segments == {"Nimal", "Gob", "OC", "Top"}

    def test_default_rate_correct(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_default_by_segment(portfolio_df)
        by_seg = {r["segment"]: r for r in result}
        # OC: L06 has default_flag=1, L05 has default_flag=0 → 50%
        assert by_seg["OC"]["default_rate_pct"] == 50.0

    def test_sorted_by_default_rate_desc(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_default_by_segment(portfolio_df)
        rates = [r["default_rate_pct"] for r in result]
        assert rates == sorted(rates, reverse=True)

    def test_fallback_to_dpd_when_no_default_flag(self, portfolio_df: pd.DataFrame) -> None:
        df = portfolio_df.drop(columns=["default_flag"])
        result = compute_default_by_segment(df, dpd_threshold=90)
        by_seg = {r["segment"]: r for r in result}
        # L06 dpd=95 > 90 → default in OC
        assert by_seg["OC"]["default_loans"] >= 1

    def test_empty_returns_empty(self) -> None:
        assert compute_default_by_segment(pd.DataFrame()) == []


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — compute_max_mora_by_segment
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeMaxMoraBySegment:
    def test_max_dpd_per_segment(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_max_mora_by_segment(portfolio_df)
        by_seg = {r["segment"]: r for r in result}
        assert by_seg["OC"]["max_dpd"] == 95    # L06
        assert by_seg["Gob"]["max_dpd"] == 45   # L04
        assert by_seg["Nimal"]["max_dpd"] == 32  # L09

    def test_sorted_by_max_dpd_desc(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_max_mora_by_segment(portfolio_df)
        maxes = [r["max_dpd"] for r in result]
        assert maxes == sorted(maxes, reverse=True)

    def test_dpd_buckets_present(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_max_mora_by_segment(portfolio_df)
        for row in result:
            assert "dpd_buckets" in row
            assert set(row["dpd_buckets"].keys()) == {"current", "1_30", "31_60", "61_90", "90_plus"}

    def test_empty_returns_empty(self) -> None:
        assert compute_max_mora_by_segment(pd.DataFrame()) == []


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — compute_churn_analysis
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeChurnAnalysis:
    def test_returns_expected_keys(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_churn_analysis(portfolio_df, snapshot_date="2026-03-27")
        assert "churn_rate_pct" in result
        assert "churned_count" in result
        assert "total_customers" in result

    def test_churn_rate_between_0_and_100(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_churn_analysis(portfolio_df, snapshot_date="2026-03-27")
        assert 0 <= result["churn_rate_pct"] <= 100

    def test_older_loans_are_churned(self, portfolio_df: pd.DataFrame) -> None:
        # Using today's date (2026-03-27), all loans are > 90 days old
        result = compute_churn_analysis(portfolio_df, snapshot_date="2026-03-27", inactivity_days=90)
        assert result["churned_count"] > 0

    def test_by_segment_includes_all_segments(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_churn_analysis(portfolio_df, snapshot_date="2026-03-27", segment_col="segment")
        segs = {r["segment"] for r in result["by_segment"]}
        assert segs.issuperset({"Nimal", "Gob"})

    def test_empty_returns_zero(self) -> None:
        result = compute_churn_analysis(pd.DataFrame())
        assert result["total_customers"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — compute_pricing_recommendations
# ══════════════════════════════════════════════════════════════════════════════

class TestComputePricingRecommendations:
    def test_returns_three_keys(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_pricing_recommendations(portfolio_df)
        assert "tier_analysis" in result
        assert "min_commission_policy" in result
        assert "segment_pricing" in result

    def test_min_commission_policy_threshold(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_pricing_recommendations(
            portfolio_df, min_commission_usd=750.0, small_loan_threshold=15_000.0
        )
        assert result["min_commission_policy"]["min_commission_usd"] == 750.0
        assert result["min_commission_policy"]["threshold_usd"] == 15_000.0

    def test_loans_affected_positive(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_pricing_recommendations(portfolio_df)
        # Loans L01 (5K), L09 (8K) are < $10K → should trigger min commission
        assert result["min_commission_policy"]["loans_affected"] >= 1

    def test_segment_pricing_per_segment(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_pricing_recommendations(portfolio_df)
        segs = {r["segment"] for r in result["segment_pricing"]}
        assert segs == {"Nimal", "Gob", "OC", "Top"}

    def test_empty_returns_empty_structure(self) -> None:
        result = compute_pricing_recommendations(pd.DataFrame())
        assert result["tier_analysis"] == []
        assert result["min_commission_policy"]["loans_affected"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# portfolio_analytics — compute_income_and_revenue
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeIncomeAndRevenue:
    def test_returns_expected_keys(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_income_and_revenue(portfolio_df)
        for key in ["interest_income_usd", "fee_income_usd", "total_revenue_usd",
                    "net_yield_pct", "total_portfolio_usd", "revenue_by_segment"]:
            assert key in result

    def test_total_revenue_is_sum_of_components(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_income_and_revenue(portfolio_df)
        expected = round(result["interest_income_usd"] + result["fee_income_usd"], 2)
        assert abs(result["total_revenue_usd"] - expected) < 0.01

    def test_net_yield_positive(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_income_and_revenue(portfolio_df)
        assert result["net_yield_pct"] > 0

    def test_segment_revenue_sums_to_total(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_income_and_revenue(portfolio_df)
        segment_sum = sum(r["total_revenue_usd"] for r in result["revenue_by_segment"])
        assert abs(segment_sum - result["total_revenue_usd"]) < 0.05

    def test_revenue_sorted_by_total_desc(self, portfolio_df: pd.DataFrame) -> None:
        result = compute_income_and_revenue(portfolio_df)
        revenues = [r["total_revenue_usd"] for r in result["revenue_by_segment"]]
        assert revenues == sorted(revenues, reverse=True)

    def test_empty_returns_zeros(self) -> None:
        result = compute_income_and_revenue(pd.DataFrame())
        assert result["total_revenue_usd"] == 0.0
