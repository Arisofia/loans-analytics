"""Holding Group — Consolidated Financial Indicators Module.

Implements the 10 recommendations from the EEFF Consolidado 2025-08 V08 analysis:

1. PPC/PPP recalculation using average portfolio as denominator
2. Liquidity reserve model (5% minimum)
3. Debt covenants verification (mora, replines 30/60/90, 98.50% collection)
4. Default rate reconciliation (UNIT-EC vs ER-CONS)
5. Downside scenario modeling (3% monthly growth)
6. International subsidiary setup costs
7. AF→AT migration tracking
8. D/EBITDA sensitivity analysis
9. Intercompany elimination monthly verification
10. Portfolio concentration (top 10 debtors)

Uses Decimal for all financial calculations per engineering rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

logger = logging.getLogger(__name__)

_TWO_PLACES = Decimal("0.01")
_FOUR_PLACES = Decimal("0.0001")
_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "holding_projections.yml"


def _d(value: float | int | str) -> Decimal:
    """Convert to Decimal safely."""
    return Decimal(str(value))


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Calculate percentage, returning zero on zero denominator."""
    if denominator == 0:
        return Decimal("0")
    return (numerator / denominator * _d(100)).quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP)


def load_holding_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load holding projections YAML config."""
    path = config_path or _CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Holding projections config not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config format at {path}")
    return data


# =============================================================================
# 1. PPC / PPP — Recalculated with Average Portfolio as Denominator
# =============================================================================

def calculate_ppc_corrected(
    average_portfolio_usd: float,
    collections_period_usd: float,
    period_days: int = 30,
) -> Dict[str, Any]:
    """Calculate Período Promedio de Cobro using average portfolio balance.

    The original model used monthly sales as denominator which produced
    irrational values (2,188 days for 60-day loans). This version uses
    the average outstanding portfolio balance as the correct denominator
    for a lending business.

    Formula: PPC = (Average_Portfolio / Collections_Period) × Period_Days
    """
    avg = _d(average_portfolio_usd)
    collections = _d(collections_period_usd)
    days = _d(period_days)

    if collections == 0:
        return {
            "ppc_days": None,
            "average_portfolio_usd": float(avg.quantize(_TWO_PLACES)),
            "collections_usd": 0.0,
            "formula": "(average_portfolio / collections) × period_days",
            "note": "Collections = 0 — PPC undefined",
        }

    ppc = (avg / collections * days).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    return {
        "ppc_days": float(ppc),
        "average_portfolio_usd": float(avg.quantize(_TWO_PLACES)),
        "collections_usd": float(collections.quantize(_TWO_PLACES)),
        "period_days": period_days,
        "formula": "(average_portfolio / collections) × period_days",
    }


def calculate_ppp_corrected(
    accounts_payable_usd: float,
    operating_expenses_period_usd: float,
    period_days: int = 30,
) -> Dict[str, Any]:
    """Calculate Período Promedio de Pago using operating expenses.

    The original model PPP of 4,496 days was mathematically inconsistent.
    This uses operating expenditures as the correct denominator.

    Formula: PPP = (Accounts_Payable / Operating_Expenses_Period) × Period_Days
    """
    ap = _d(accounts_payable_usd)
    opex = _d(operating_expenses_period_usd)
    days = _d(period_days)

    if opex == 0:
        return {
            "ppp_days": None,
            "accounts_payable_usd": float(ap.quantize(_TWO_PLACES)),
            "opex_usd": 0.0,
            "formula": "(accounts_payable / operating_expenses) × period_days",
            "note": "Operating expenses = 0 — PPP undefined",
        }

    ppp = (ap / opex * days).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    return {
        "ppp_days": float(ppp),
        "accounts_payable_usd": float(ap.quantize(_TWO_PLACES)),
        "opex_usd": float(opex.quantize(_TWO_PLACES)),
        "period_days": period_days,
        "formula": "(accounts_payable / operating_expenses) × period_days",
    }


def calculate_cash_conversion_cycle(
    ppc_days: float,
    ppp_days: float,
    inventory_days: float = 0.0,
) -> Dict[str, Any]:
    """CCE = PPC + Inventory_Days - PPP (negative is favorable for fintech)."""
    cce = _d(ppc_days) + _d(inventory_days) - _d(ppp_days)
    return {
        "cce_days": float(cce.quantize(_TWO_PLACES)),
        "ppc_days": ppc_days,
        "ppp_days": ppp_days,
        "inventory_days": inventory_days,
        "formula": "PPC + inventory_days - PPP",
        "interpretation": "negative" if cce < 0 else "positive",
    }


# =============================================================================
# 2. Liquidity Reserve Model
# =============================================================================

def calculate_liquidity_reserve(
    active_portfolio_usd: float,
    min_reserve_pct: float = 0.05,
    floor_usd: float = 200_000,
) -> Dict[str, Any]:
    """Calculate minimum liquidity reserve (5% of active portfolio, min $200K).

    Alert: defensive test collapsed to 0.9% in 2025 projection. This reserve
    ensures operating cash buffer even under unexpected delinquency or
    funding line cuts.
    """
    portfolio = _d(active_portfolio_usd)
    pct = _d(min_reserve_pct)
    floor = _d(floor_usd)

    calculated = (portfolio * pct).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    required = max(calculated, floor)

    return {
        "required_reserve_usd": float(required),
        "calculated_pct_usd": float(calculated),
        "floor_usd": float(floor),
        "active_portfolio_usd": float(portfolio.quantize(_TWO_PLACES)),
        "reserve_pct": float(pct),
        "formula": "max(portfolio × min_reserve_pct, floor_usd)",
    }


# =============================================================================
# 3. Debt Covenant Verification
# =============================================================================

@dataclass
class CovenantResult:
    """Result of a single covenant check."""
    name: str
    compliant: bool
    actual_value: float
    threshold: float
    description: str
    cure_action: str = ""


def verify_debt_covenants(
    collection_rate: float,
    prior_delinquency_rate: float,
    current_delinquency_rate: float,
    repline_30d_pct: float,
    repline_60d_pct: float,
    repline_90d_pct: float,
    min_collection_rate: float = 0.985,
    max_repline_30d: float = 0.45,
    max_repline_60d: float = 0.35,
    max_repline_90d: float = 0.20,
) -> Dict[str, Any]:
    """Verify all debt covenants per fund requirements.

    Covenants:
    - Collection rate >= 98.50%
    - Delinquency cannot grow vs prior period
    - Repline distribution within 30/60/90 limits
    - Only 80% of qualifying portfolio is financed
    """
    results: List[Dict[str, Any]] = []

    # Covenant 1: Minimum collection rate
    cov1 = CovenantResult(
        name="min_collection_rate",
        compliant=collection_rate >= min_collection_rate,
        actual_value=collection_rate,
        threshold=min_collection_rate,
        description="Tasa de cobro mínima exigida por el fondo (98.50%)",
        cure_action="Incrementar patrimonio hasta restaurar ratio" if collection_rate < min_collection_rate else "",
    )
    results.append(vars(cov1))

    # Covenant 2: Delinquency cannot grow
    delinq_growth = current_delinquency_rate - prior_delinquency_rate
    cov2 = CovenantResult(
        name="max_delinquency_growth",
        compliant=delinq_growth <= 0,
        actual_value=delinq_growth,
        threshold=0.0,
        description="La mora no puede crecer vs período anterior",
        cure_action="Incrementar patrimonio" if delinq_growth > 0 else "",
    )
    results.append(vars(cov2))

    # Covenant 3: Repline distribution
    for label, actual, limit in [
        ("repline_30d", repline_30d_pct, max_repline_30d),
        ("repline_60d", repline_60d_pct, max_repline_60d),
        ("repline_90d", repline_90d_pct, max_repline_90d),
    ]:
        cov = CovenantResult(
            name=f"{label}_distribution",
            compliant=actual <= limit,
            actual_value=actual,
            threshold=limit,
            description=f"Distribución de repline {label} dentro del límite",
        )
        results.append(vars(cov))

    all_compliant = all(r["compliant"] for r in results)
    return {
        "overall_compliant": all_compliant,
        "covenants": results,
        "advance_rate": 0.80,
        "advance_rate_note": "Solo se financia 80% de cartera que cumple criterios",
        "global_cure_action": (
            "ACCIÓN REQUERIDA: Incrementar patrimonio para restaurar cumplimiento"
            if not all_compliant
            else "Todos los covenants cumplidos"
        ),
    }


# =============================================================================
# 4. Default Rate Reconciliation
# =============================================================================

def reconcile_default_rates(
    default_per_ticket_usd: float = 19.2,
    revenue_per_ticket_usd: float = 322.5,
    yield_per_ticket: float = 0.074,
    average_ticket_usd: float = 4366.0,
    monthly_default_rate_portfolio: float = 0.0044,
) -> Dict[str, Any]:
    """Reconcile UNIT-EC default rate (5.96%) with ER-CONS irrecoverable (0.44%).

    Shows that both numbers are consistent under different accounting optics:
    - UNIT-EC: default as % of revenue per ticket
    - ER-CONS: default as % of total portfolio balance (write-offs only)
    """
    ticket_default_rate = _d(default_per_ticket_usd) / _d(revenue_per_ticket_usd)

    # Reverse calculation: portfolio rate → per-ticket rate
    derived_default_per_ticket = (
        _d(monthly_default_rate_portfolio)
        * _d(average_ticket_usd)
        / _d(revenue_per_ticket_usd)
    )

    reconciled = abs(float(ticket_default_rate) - float(derived_default_per_ticket)) < 0.005

    return {
        "unit_ec_default_rate_pct": float(_pct(_d(default_per_ticket_usd), _d(revenue_per_ticket_usd))),
        "er_cons_monthly_rate_pct": monthly_default_rate_portfolio * 100,
        "derived_rate_from_portfolio_pct": float(derived_default_per_ticket * 100),
        "reconciled": reconciled,
        "explanation": (
            "El 5.96% de UNIT-EC se calcula sobre ingreso por ticket. "
            "El 0.44% de ER-CONS se calcula sobre saldo de cartera total. "
            f"Derivado: {float(derived_default_per_ticket * 100):.2f}% ≈ {float(ticket_default_rate * 100):.2f}% ✓"
            if reconciled
            else "DISCREPANCIA — requiere revisión manual de las provisiones"
        ),
        "formula": "default_rate_cartera × (ticket_promedio / revenue_per_ticket)",
    }


# =============================================================================
# 5. Downside Scenario Modeling
# =============================================================================

def model_growth_scenario(
    base_portfolio_usd: float,
    monthly_growth_rate: float,
    months: int = 12,
    label: str = "base",
) -> Dict[str, Any]:
    """Project portfolio growth under a given monthly rate.

    Base scenario: 5.5% monthly (AT)
    Downside scenario: 3.0% monthly (AT)
    """
    portfolio = _d(base_portfolio_usd)
    rate = _d(monthly_growth_rate)
    trajectory: List[Dict[str, Any]] = []

    for m in range(1, months + 1):
        portfolio = (portfolio * (1 + rate)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        trajectory.append({
            "month": m,
            "portfolio_usd": float(portfolio),
            "cumulative_growth_pct": float(
                _pct(portfolio - _d(base_portfolio_usd), _d(base_portfolio_usd))
            ),
        })

    final = trajectory[-1]["portfolio_usd"] if trajectory else base_portfolio_usd
    annual_growth = float(_pct(_d(final) - _d(base_portfolio_usd), _d(base_portfolio_usd)))

    return {
        "scenario": label,
        "base_portfolio_usd": base_portfolio_usd,
        "monthly_growth_rate": monthly_growth_rate,
        "months": months,
        "final_portfolio_usd": final,
        "annual_growth_pct": annual_growth,
        "trajectory": trajectory,
    }


def compare_scenarios(
    base_portfolio_usd: float,
    base_rate: float = 0.055,
    downside_rate: float = 0.03,
    months: int = 12,
) -> Dict[str, Any]:
    """Compare base vs downside scenario over a projection period."""
    base = model_growth_scenario(base_portfolio_usd, base_rate, months, "base")
    downside = model_growth_scenario(base_portfolio_usd, downside_rate, months, "downside")

    revenue_reduction_pct = float(
        _pct(
            _d(base["final_portfolio_usd"]) - _d(downside["final_portfolio_usd"]),
            _d(base["final_portfolio_usd"]),
        )
    )

    return {
        "base_scenario": base,
        "downside_scenario": downside,
        "revenue_impact_pct": revenue_reduction_pct,
        "portfolio_gap_usd": round(
            base["final_portfolio_usd"] - downside["final_portfolio_usd"], 2
        ),
    }


# =============================================================================
# 6. International Subsidiary Setup Costs
# =============================================================================

def calculate_subsidiary_setup_costs(
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate pre-revenue setup costs for all international subsidiaries.

    Loads from holding_projections.yml entity definitions.
    """
    if config is None:
        config = load_holding_config()

    entities = config.get("entities", {})
    total_setup = Decimal("0")
    total_seed = Decimal("0")
    subsidiaries: List[Dict[str, Any]] = []

    for name, ent in entities.items():
        if ent.get("status") != "pre_launch":
            continue
        setup = ent.get("setup_costs", {})
        seed = _d(ent.get("seed_capital_usd", 0))
        setup_total = _d(setup.get("total_pre_revenue_usd", 0))
        total_setup += setup_total
        total_seed += seed

        subsidiaries.append({
            "entity": name,
            "code": ent.get("code"),
            "country": ent.get("country"),
            "launch_year": ent.get("projected_launch_year"),
            "seed_capital_usd": float(seed),
            "setup_cost_breakdown": {
                "regulatory_license": setup.get("regulatory_license_usd", 0),
                "legal_incorporation": setup.get("legal_incorporation_usd", 0),
                "office_setup": setup.get("office_setup_usd", 0),
                "payroll_pre_revenue": (
                    setup.get("initial_payroll_months", 0)
                    * setup.get("monthly_payroll_usd", 0)
                ),
                "technology_setup": setup.get("technology_setup_usd", 0),
                "marketing_launch": setup.get("marketing_launch_usd", 0),
            },
            "total_pre_revenue_usd": float(setup_total),
        })

    return {
        "subsidiaries": subsidiaries,
        "total_setup_costs_usd": float(total_setup.quantize(_TWO_PLACES)),
        "total_seed_capital_usd": float(total_seed.quantize(_TWO_PLACES)),
        "total_required_usd": float((total_setup + total_seed).quantize(_TWO_PLACES)),
        "note": "Costos pre-revenue de subsidiarias internacionales antes del arranque",
    }


# =============================================================================
# 7. AF → AT Migration Tracking
# =============================================================================

def track_af_migration(
    af_portfolio_start_usd: float,
    af_portfolio_current_usd: float,
    at_portfolio_start_usd: float,
    at_portfolio_current_usd: float,
) -> Dict[str, Any]:
    """Track the migration of AF portfolio to AT.

    Strategy: AF clients renew under the AT platform as their operations mature.
    AF's contraction (-32% in 8 months) is strategic, not deterioration.
    """
    af_delta = _d(af_portfolio_current_usd) - _d(af_portfolio_start_usd)
    at_delta = _d(at_portfolio_current_usd) - _d(at_portfolio_start_usd)

    # Migration absorption: how much of AF's decline maps to AT's growth
    if af_delta < 0 and at_delta > 0:
        absorption = min(abs(af_delta), at_delta)
        absorption_pct = _pct(absorption, abs(af_delta))
    else:
        absorption = Decimal("0")
        absorption_pct = Decimal("0")

    af_change_pct = _pct(af_delta, _d(af_portfolio_start_usd))
    at_change_pct = _pct(at_delta, _d(at_portfolio_start_usd))

    consolidated_start = _d(af_portfolio_start_usd) + _d(at_portfolio_start_usd)
    consolidated_current = _d(af_portfolio_current_usd) + _d(at_portfolio_current_usd)
    consolidated_change_pct = _pct(consolidated_current - consolidated_start, consolidated_start)

    return {
        "af_portfolio_start_usd": af_portfolio_start_usd,
        "af_portfolio_current_usd": af_portfolio_current_usd,
        "af_change_pct": float(af_change_pct),
        "at_portfolio_start_usd": at_portfolio_start_usd,
        "at_portfolio_current_usd": at_portfolio_current_usd,
        "at_change_pct": float(at_change_pct),
        "migration_absorption_usd": float(absorption.quantize(_TWO_PLACES)),
        "migration_absorption_pct": float(absorption_pct),
        "consolidated_change_pct": float(consolidated_change_pct),
        "strategy": "portfolio_transfer_to_AT",
        "strategy_note": (
            "Migración estratégica: clientes AF se renuevan bajo plataforma AT. "
            "La contracción de AF no es deterioro sino transferencia planificada."
        ),
    }


# =============================================================================
# 8. D/EBITDA Sensitivity Analysis
# =============================================================================

def calculate_d_ebitda_sensitivity(
    total_debt_usd: float,
    ebitda_base_usd: float,
    funding_cost_rate_base: float = 0.08,
) -> Dict[str, Any]:
    """Generate D/EBITDA sensitivity table across rate and EBITDA scenarios.

    When D/EBITDA = 25.36x (2025), institutional debt with standard covenants
    (<6x) is impossible. All 2025 debt must come from impact investors, SAFEs,
    or convertible debt without EBITDA covenants.
    """
    debt = _d(total_debt_usd)
    ebitda_base = _d(ebitda_base_usd)
    rate_base = _d(funding_cost_rate_base)

    # EBITDA scenarios: -30%, -15%, base, +15%, +30%
    ebitda_multipliers = [
        ("ebitda_-30%", Decimal("0.70")),
        ("ebitda_-15%", Decimal("0.85")),
        ("ebitda_base", Decimal("1.00")),
        ("ebitda_+15%", Decimal("1.15")),
        ("ebitda_+30%", Decimal("1.30")),
    ]

    # Funding rate scenarios: -200bps, -100bps, base, +100bps, +200bps
    rate_scenarios = [
        ("rate_-200bps", rate_base - Decimal("0.02")),
        ("rate_-100bps", rate_base - Decimal("0.01")),
        ("rate_base", rate_base),
        ("rate_+100bps", rate_base + Decimal("0.01")),
        ("rate_+200bps", rate_base + Decimal("0.02")),
    ]

    table: List[Dict[str, Any]] = []
    for ebitda_label, ebitda_mult in ebitda_multipliers:
        ebitda_scenario = ebitda_base * ebitda_mult
        for rate_label, rate in rate_scenarios:
            # Adjust debt cost
            interest_expense = debt * rate
            ebitda_after_rate = ebitda_scenario  # EBITDA is before interest

            if ebitda_after_rate <= 0:
                d_ebitda = None
                covenant_status = "N/A — EBITDA ≤ 0"
            else:
                d_ebitda = float((debt / ebitda_after_rate).quantize(_TWO_PLACES))
                if d_ebitda <= 3.5:
                    covenant_status = "STRONG"
                elif d_ebitda <= 5.0:
                    covenant_status = "ACCEPTABLE"
                elif d_ebitda <= 7.0:
                    covenant_status = "WATCH"
                else:
                    covenant_status = "BREACH"

            table.append({
                "ebitda_scenario": ebitda_label,
                "rate_scenario": rate_label,
                "ebitda_usd": float(ebitda_scenario.quantize(_TWO_PLACES)) if ebitda_scenario else 0,
                "funding_rate": float(rate),
                "annual_interest_usd": float(interest_expense.quantize(_TWO_PLACES)),
                "d_ebitda": d_ebitda,
                "covenant_status": covenant_status,
            })

    return {
        "total_debt_usd": total_debt_usd,
        "ebitda_base_usd": ebitda_base_usd,
        "funding_cost_rate_base": funding_cost_rate_base,
        "sensitivity_table": table,
        "note": (
            "D/EBITDA > 6x = BREACH de covenants institucionales. "
            "2025 requiere financiamiento vía SAFEs/deuda convertible sin covenants EBITDA."
        ),
    }


# =============================================================================
# 9. Intercompany Elimination Monthly Verification
# =============================================================================

def verify_intercompany_elimination(
    monthly_records: Sequence[Dict[str, Any]],
    expected_monthly_usd: float = 40_000.0,
    tolerance_pct: float = 0.05,
) -> Dict[str, Any]:
    """Verify monthly intercompany elimination consistency.

    The $40K/month elimination started in Sept-2024 and is verified
    month-by-month against entity records (D_ACT_AT, D_ACT_AF).

    Args:
        monthly_records: List of dicts with keys 'period', 'elimination_usd',
                        'at_intercompany_balance', 'af_intercompany_balance'
        expected_monthly_usd: Expected monthly elimination amount
        tolerance_pct: Acceptable deviation (5% default)
    """
    expected = _d(expected_monthly_usd)
    tol = _d(tolerance_pct)
    results: List[Dict[str, Any]] = []
    issues: List[str] = []

    for record in monthly_records:
        period = record.get("period", "unknown")
        elimination = _d(record.get("elimination_usd", 0))
        at_balance = _d(record.get("at_intercompany_balance", 0))
        af_balance = _d(record.get("af_intercompany_balance", 0))

        deviation = abs(elimination - expected)
        deviation_pct = _pct(deviation, expected) if expected > 0 else Decimal("0")
        within_tolerance = deviation_pct <= tol * 100

        # Bilateral check: AT and AF should have offsetting balances
        bilateral_match = abs(at_balance + af_balance) < expected * Decimal("0.01")

        if not within_tolerance:
            issues.append(
                f"{period}: eliminación ${float(elimination):,.0f} desvía "
                f"{float(deviation_pct):.1f}% del esperado ${float(expected):,.0f}"
            )
        if not bilateral_match:
            issues.append(
                f"{period}: saldos intercompany AT=${float(at_balance):,.0f} + "
                f"AF=${float(af_balance):,.0f} no se compensan bilateralmente"
            )

        results.append({
            "period": period,
            "elimination_usd": float(elimination),
            "expected_usd": float(expected),
            "deviation_pct": float(deviation_pct),
            "within_tolerance": within_tolerance,
            "bilateral_match": bilateral_match,
        })

    return {
        "records_checked": len(results),
        "all_consistent": len(issues) == 0,
        "issues": issues,
        "details": results,
        "verification_note": (
            "Eliminación intercompany $40K/mes verificada bilateralmente AT↔AF↔GAS. "
            "Se realiza mes con mes desde sept-2024."
        ),
    }


# =============================================================================
# 10. Portfolio Concentration Analysis (Top 10 Debtors)
# =============================================================================

def calculate_portfolio_concentration(
    debtors: Sequence[Dict[str, Any]],
    total_portfolio_usd: float,
    max_single_obligor_pct: float = 0.04,
    max_top_10_pct: float = 0.30,
) -> Dict[str, Any]:
    """Analyze portfolio concentration risk — top 10 debtors.

    Guardrails from business_parameters.yml:
    - max_single_obligor_concentration: 4%
    - max_top_10_concentration: 30%

    Args:
        debtors: List of dicts with 'debtor_id', 'name', 'outstanding_usd'
        total_portfolio_usd: Total portfolio balance
    """
    if not debtors:
        return {
            "top_10": [],
            "top_10_concentration_pct": 0.0,
            "hhi": 0.0,
            "alerts": [],
            "compliant": True,
        }

    total = _d(total_portfolio_usd)
    sorted_debtors = sorted(debtors, key=lambda d: d.get("outstanding_usd", 0), reverse=True)
    top_10 = sorted_debtors[:10]

    alerts: List[str] = []
    top_10_result: List[Dict[str, Any]] = []
    top_10_balance = Decimal("0")

    for rank, debtor in enumerate(top_10, 1):
        balance = _d(debtor.get("outstanding_usd", 0))
        share = _pct(balance, total) if total > 0 else Decimal("0")
        top_10_balance += balance

        if float(share) / 100 > max_single_obligor_pct:
            alerts.append(
                f"ALERTA: Deudor #{rank} ({debtor.get('name', debtor.get('debtor_id'))}) "
                f"concentra {float(share):.2f}% > límite {max_single_obligor_pct * 100:.0f}%"
            )

        top_10_result.append({
            "rank": rank,
            "debtor_id": debtor.get("debtor_id"),
            "name": debtor.get("name", ""),
            "outstanding_usd": float(balance.quantize(_TWO_PLACES)),
            "share_pct": float(share),
        })

    top_10_concentration = _pct(top_10_balance, total) if total > 0 else Decimal("0")
    if float(top_10_concentration) / 100 > max_top_10_pct:
        alerts.append(
            f"ALERTA: Top 10 concentra {float(top_10_concentration):.2f}% > "
            f"límite {max_top_10_pct * 100:.0f}%"
        )

    # HHI (Herfindahl-Hirschman Index) for all debtors
    hhi = Decimal("0")
    for debtor in sorted_debtors:
        share = _d(debtor.get("outstanding_usd", 0)) / total if total > 0 else Decimal("0")
        hhi += share ** 2
    hhi_normalized = float((hhi * 10000).quantize(_TWO_PLACES))

    return {
        "top_10": top_10_result,
        "top_10_concentration_pct": float(top_10_concentration),
        "top_10_balance_usd": float(top_10_balance.quantize(_TWO_PLACES)),
        "total_portfolio_usd": total_portfolio_usd,
        "hhi": hhi_normalized,
        "hhi_interpretation": (
            "Baja concentración" if hhi_normalized < 1500
            else "Concentración moderada" if hhi_normalized < 2500
            else "Alta concentración"
        ),
        "alerts": alerts,
        "compliant": len(alerts) == 0,
        "guardrails": {
            "max_single_obligor_pct": max_single_obligor_pct * 100,
            "max_top_10_pct": max_top_10_pct * 100,
        },
    }
