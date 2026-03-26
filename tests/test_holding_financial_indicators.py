"""Tests for holding_financial_indicators module.

Validates all 10 recommendations from the EEFF Consolidado analysis.
"""

from __future__ import annotations

import pytest
from backend.python.kpis.holding_financial_indicators import (
    calculate_cash_conversion_cycle,
    calculate_d_ebitda_sensitivity,
    calculate_liquidity_reserve,
    calculate_portfolio_concentration,
    calculate_ppc_corrected,
    calculate_ppp_corrected,
    calculate_subsidiary_setup_costs,
    compare_scenarios,
    model_growth_scenario,
    reconcile_default_rates,
    track_af_migration,
    verify_debt_covenants,
    verify_intercompany_elimination,
)


# ===========================================================================
# 1. PPC / PPP Corrected
# ===========================================================================

class TestPPCCorrected:
    def test_normal_calculation(self):
        result = calculate_ppc_corrected(
            average_portfolio_usd=7_730_000,
            collections_period_usd=1_300_000,
            period_days=30,
        )
        assert result["ppc_days"] is not None
        # Should be ~178 days, NOT 2,188
        assert result["ppc_days"] < 200
        assert result["ppc_days"] > 100

    def test_zero_collections(self):
        result = calculate_ppc_corrected(
            average_portfolio_usd=1_000_000,
            collections_period_usd=0,
        )
        assert result["ppc_days"] is None


class TestPPPCorrected:
    def test_normal_calculation(self):
        result = calculate_ppp_corrected(
            accounts_payable_usd=180_000,
            operating_expenses_period_usd=120_000,
            period_days=30,
        )
        assert result["ppp_days"] is not None
        # Should be ~45 days, NOT 4,496
        assert result["ppp_days"] < 100

    def test_zero_opex(self):
        result = calculate_ppp_corrected(
            accounts_payable_usd=50_000,
            operating_expenses_period_usd=0,
        )
        assert result["ppp_days"] is None


class TestCashConversionCycle:
    def test_negative_cce_fintech(self):
        result = calculate_cash_conversion_cycle(
            ppc_days=178.0,
            ppp_days=45.0,
        )
        # PPC > PPP → positive CCE for lending (but reasonable)
        assert result["cce_days"] == 133.0
        assert result["interpretation"] == "positive"

    def test_favorable_cce(self):
        result = calculate_cash_conversion_cycle(ppc_days=30, ppp_days=60)
        assert result["cce_days"] == -30.0
        assert result["interpretation"] == "negative"


# ===========================================================================
# 2. Liquidity Reserve
# ===========================================================================

class TestLiquidityReserve:
    def test_5pct_reserve(self):
        result = calculate_liquidity_reserve(active_portfolio_usd=7_730_000)
        assert result["required_reserve_usd"] == 386_500.0

    def test_floor_applies(self):
        # Small portfolio → floor kicks in
        result = calculate_liquidity_reserve(active_portfolio_usd=1_000_000)
        assert result["required_reserve_usd"] == 200_000.0

    def test_large_portfolio(self):
        result = calculate_liquidity_reserve(active_portfolio_usd=201_000_000)
        assert result["required_reserve_usd"] == 10_050_000.0


# ===========================================================================
# 3. Debt Covenants
# ===========================================================================

class TestDebtCovenants:
    def test_all_compliant(self):
        result = verify_debt_covenants(
            collection_rate=0.99,
            prior_delinquency_rate=0.02,
            current_delinquency_rate=0.015,
            repline_30d_pct=0.40,
            repline_60d_pct=0.30,
            repline_90d_pct=0.15,
        )
        assert result["overall_compliant"] is True

    def test_collection_rate_breach(self):
        result = verify_debt_covenants(
            collection_rate=0.97,  # Below 98.50%
            prior_delinquency_rate=0.02,
            current_delinquency_rate=0.015,
            repline_30d_pct=0.40,
            repline_60d_pct=0.30,
            repline_90d_pct=0.15,
        )
        assert result["overall_compliant"] is False
        assert any(c["name"] == "min_collection_rate" and not c["compliant"]
                   for c in result["covenants"])

    def test_delinquency_growth_breach(self):
        result = verify_debt_covenants(
            collection_rate=0.99,
            prior_delinquency_rate=0.02,
            current_delinquency_rate=0.025,  # Growing
            repline_30d_pct=0.40,
            repline_60d_pct=0.30,
            repline_90d_pct=0.15,
        )
        assert result["overall_compliant"] is False

    def test_advance_rate_documented(self):
        result = verify_debt_covenants(
            collection_rate=0.99,
            prior_delinquency_rate=0.02,
            current_delinquency_rate=0.015,
            repline_30d_pct=0.40,
            repline_60d_pct=0.30,
            repline_90d_pct=0.15,
        )
        assert result["advance_rate"] == 0.80


# ===========================================================================
# 4. Default Rate Reconciliation
# ===========================================================================

class TestDefaultRateReconciliation:
    def test_reconciliation_matches(self):
        result = reconcile_default_rates()
        assert result["reconciled"] is True
        assert abs(result["unit_ec_default_rate_pct"] - 5.95) < 0.5

    def test_er_cons_rate(self):
        result = reconcile_default_rates()
        assert result["er_cons_monthly_rate_pct"] == pytest.approx(0.44, abs=0.01)


# ===========================================================================
# 5. Downside Scenario
# ===========================================================================

class TestDownsideScenario:
    def test_base_vs_downside(self):
        result = compare_scenarios(
            base_portfolio_usd=7_730_000,
            base_rate=0.055,
            downside_rate=0.03,
            months=12,
        )
        base_final = result["base_scenario"]["final_portfolio_usd"]
        down_final = result["downside_scenario"]["final_portfolio_usd"]
        assert base_final > down_final
        assert result["portfolio_gap_usd"] > 0

    def test_growth_trajectory(self):
        result = model_growth_scenario(
            base_portfolio_usd=7_730_000,
            monthly_growth_rate=0.03,
            months=12,
            label="downside",
        )
        assert len(result["trajectory"]) == 12
        assert result["trajectory"][-1]["portfolio_usd"] > 7_730_000

    def test_downside_reduces_revenue_roughly_40pct(self):
        result = compare_scenarios(
            base_portfolio_usd=7_730_000,
            base_rate=0.055,
            downside_rate=0.03,
            months=12,
        )
        # The base grows ~90% annually, downside ~42%
        # Revenue impact should be significant
        assert result["revenue_impact_pct"] > 20


# ===========================================================================
# 6. Subsidiary Setup Costs
# ===========================================================================

class TestSubsidiarySetupCosts:
    def test_loads_from_config(self):
        result = calculate_subsidiary_setup_costs()
        assert len(result["subsidiaries"]) > 0
        assert result["total_setup_costs_usd"] > 0
        assert result["total_seed_capital_usd"] > 0

    def test_all_pre_launch(self):
        result = calculate_subsidiary_setup_costs()
        for sub in result["subsidiaries"]:
            assert sub["launch_year"] is not None
            assert sub["seed_capital_usd"] > 0


# ===========================================================================
# 7. AF → AT Migration
# ===========================================================================

class TestAFMigration:
    def test_migration_tracking(self):
        result = track_af_migration(
            af_portfolio_start_usd=1_590_000,
            af_portfolio_current_usd=1_080_000,
            at_portfolio_start_usd=2_270_000,
            at_portfolio_current_usd=6_650_000,
        )
        assert result["af_change_pct"] < 0  # AF contracting
        assert result["at_change_pct"] > 0  # AT growing
        assert result["consolidated_change_pct"] > 0
        assert result["migration_absorption_usd"] > 0

    def test_strategy_is_documented(self):
        result = track_af_migration(
            af_portfolio_start_usd=1_590_000,
            af_portfolio_current_usd=1_080_000,
            at_portfolio_start_usd=2_270_000,
            at_portfolio_current_usd=6_650_000,
        )
        assert result["strategy"] == "portfolio_transfer_to_AT"


# ===========================================================================
# 8. D/EBITDA Sensitivity
# ===========================================================================

class TestDEBITDASensitivity:
    def test_sensitivity_table(self):
        result = calculate_d_ebitda_sensitivity(
            total_debt_usd=13_700_000,
            ebitda_base_usd=1_950_000,
        )
        table = result["sensitivity_table"]
        assert len(table) == 25  # 5×5 matrix

    def test_base_case_reasonable(self):
        result = calculate_d_ebitda_sensitivity(
            total_debt_usd=13_700_000,
            ebitda_base_usd=1_950_000,
        )
        base_entry = [
            r for r in result["sensitivity_table"]
            if r["ebitda_scenario"] == "ebitda_base" and r["rate_scenario"] == "rate_base"
        ][0]
        assert base_entry["d_ebitda"] == pytest.approx(7.03, abs=0.1)
        assert base_entry["covenant_status"] in ("WATCH", "BREACH")

    def test_zero_ebitda(self):
        result = calculate_d_ebitda_sensitivity(
            total_debt_usd=10_000_000,
            ebitda_base_usd=0,
        )
        for entry in result["sensitivity_table"]:
            assert entry["d_ebitda"] is None


# ===========================================================================
# 9. Intercompany Elimination
# ===========================================================================

class TestIntercompanyElimination:
    def test_all_consistent(self):
        records = [
            {"period": f"2025-{m:02d}", "elimination_usd": 40000,
             "at_intercompany_balance": 40000, "af_intercompany_balance": -40000}
            for m in range(1, 9)
        ]
        result = verify_intercompany_elimination(records)
        assert result["all_consistent"] is True
        assert result["records_checked"] == 8

    def test_deviation_flagged(self):
        records = [
            {"period": "2025-01", "elimination_usd": 40000,
             "at_intercompany_balance": 40000, "af_intercompany_balance": -40000},
            {"period": "2025-02", "elimination_usd": 35000,  # Deviation
             "at_intercompany_balance": 35000, "af_intercompany_balance": -35000},
        ]
        result = verify_intercompany_elimination(records)
        assert result["all_consistent"] is False
        assert len(result["issues"]) > 0


# ===========================================================================
# 10. Portfolio Concentration
# ===========================================================================

class TestPortfolioConcentration:
    def test_compliant_portfolio(self):
        debtors = [
            {"debtor_id": f"D{i}", "outstanding_usd": 100_000}
            for i in range(50)
        ]
        result = calculate_portfolio_concentration(
            debtors=debtors,
            total_portfolio_usd=5_000_000,
        )
        assert result["compliant"] is True
        assert len(result["top_10"]) == 10

    def test_single_obligor_breach(self):
        debtors = [
            {"debtor_id": "D1", "name": "Big Client", "outstanding_usd": 500_000},
            {"debtor_id": "D2", "outstanding_usd": 50_000},
        ]
        result = calculate_portfolio_concentration(
            debtors=debtors,
            total_portfolio_usd=1_000_000,
        )
        # D1 = 50% > 4% limit
        assert result["compliant"] is False
        assert len(result["alerts"]) > 0

    def test_hhi_calculation(self):
        debtors = [
            {"debtor_id": f"D{i}", "outstanding_usd": 100}
            for i in range(100)
        ]
        result = calculate_portfolio_concentration(
            debtors=debtors,
            total_portfolio_usd=10_000,
        )
        # 100 equal debtors → HHI = 100 × (1/100)^2 × 10000 = 100
        assert result["hhi"] == pytest.approx(100.0, abs=1)
        assert result["hhi_interpretation"] == "Baja concentración"

    def test_empty_portfolio(self):
        result = calculate_portfolio_concentration(
            debtors=[],
            total_portfolio_usd=0,
        )
        assert result["compliant"] is True
        assert result["top_10"] == []
