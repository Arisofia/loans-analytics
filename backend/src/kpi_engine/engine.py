from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

import pandas as pd

from backend.src.contracts.metric_schema import MetricResult
from backend.src.kpi_engine import cohorts, revenue, risk, unit_economics


def _mr(metric_id: str, name: str, value: Decimal | float, unit: str, mart: str, owner: str) -> MetricResult:
    # Ensure all values passed to MetricResult are converted to float for JSON compatibility
    # but the internal computation remains Decimal-safe.
    return MetricResult(
        metric_id=metric_id,
        metric_name=name,
        value=float(value) if isinstance(value, Decimal) else value,
        unit=unit,
        as_of_date=str(date.today()),
        source_mart=mart,
        owner=owner,
    )


def run_metric_engine(
    marts: Dict[str, pd.DataFrame],
    quality_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    portfolio = marts.get("portfolio_mart", pd.DataFrame())
    finance = marts.get("finance_mart", pd.DataFrame())
    sales = marts.get("sales_mart", pd.DataFrame())
    disbursements = marts.get("disbursements_mart", marts.get("dim_loan", marts.get("loans", pd.DataFrame())))
    payments = marts.get("payments_mart", marts.get("fact_real_payment", marts.get("payments", pd.DataFrame())))

    executive: List[MetricResult] = []
    pricing: List[MetricResult] = []

    # Risk
    risk_metrics: List[MetricResult] = [
        _mr("par30", "PAR 30", risk.compute_par30(portfolio), "ratio", "portfolio", "risk"),
    ]
    risk_metrics.extend(
        (
            _mr("par60", "PAR 60", risk.compute_par60(portfolio), "ratio", "portfolio", "risk"),
            _mr("par90", "PAR 90", risk.compute_par90(portfolio), "ratio", "portfolio", "risk"),
            _mr("expected_loss", "Expected Loss", risk.compute_expected_loss(portfolio), "currency", "portfolio", "risk"),
            _mr("npl_ratio", "NPL Ratio", risk.compute_npl_ratio(portfolio), "ratio", "portfolio", "risk"),
            _mr("default_rate_by_count", "Default Rate By Count", risk.compute_default_rate_by_count(portfolio), "ratio", "portfolio", "risk"),
            _mr("default_rate_by_balance", "Default Rate By Balance", risk.compute_default_rate_by_balance(portfolio), "ratio", "portfolio", "risk"),
            _mr("provision_coverage_ratio", "Provision Coverage Ratio", risk.compute_provision_coverage_ratio(portfolio, finance), "ratio", "finance", "risk"),
        )
    )

    # Revenue / pricing
    pricing.extend(
        (
            _mr("net_yield", "Net Yield", revenue.compute_net_yield(finance), "ratio", "finance", "cfo"),
            _mr("spread", "Spread", revenue.compute_spread(finance), "ratio", "finance", "cfo"),
            _mr("portfolio_yield", "Portfolio Yield", revenue.compute_portfolio_yield(portfolio), "percentage", "portfolio", "cfo"),
            _mr("effective_interest_rate", "Effective Interest Rate", revenue.compute_eir(portfolio), "ratio", "portfolio", "cfo"),
        )
    )
    true_irr = revenue.compute_portfolio_irr_true(disbursements, payments)
    if true_irr is not None:
        pricing.append(_mr("portfolio_irr", "Portfolio IRR", true_irr, "ratio", "cashflow", "cfo"))
    else:
        pricing.append(_mr("portfolio_irr_proxy", "Portfolio IRR Proxy", revenue.compute_portfolio_irr_proxy(finance), "ratio", "finance", "cfo"))

    # Unit economics → executive
    executive.extend(
        (
            _mr("avg_ticket", "Avg Ticket", unit_economics.compute_avg_ticket(sales), "currency", "sales", "commercial"),
            _mr("win_rate", "Win Rate", unit_economics.compute_win_rate(sales), "ratio", "sales", "commercial"),
            _mr("contribution_margin", "Contribution Margin", unit_economics.compute_contribution_margin(finance), "currency", "finance", "cfo"),
        )
    )

    # Cohorts
    if {"cohort", "default_flag"}.issubset(portfolio.columns):
        cohort_curve = cohorts.build_cohort_default_curve(portfolio)
    else:
        cohort_curve = []
    if {"vintage", "days_past_due", "default_flag"}.intersection(portfolio.columns):
        try:
            vintage_summary = cohorts.build_vintage_quality_summary(portfolio)
        except KeyError:
            vintage_summary = []
    else:
        vintage_summary = []

    return {
        "executive_metrics": executive,
        "risk_metrics": risk_metrics,
        "pricing_metrics": pricing,
        "cohort_outputs": {
            "default_curve": cohort_curve,
            "vintage_summary": vintage_summary,
        },
    }


def flatten_metric_result_groups(metric_groups: Dict[str, Any]) -> Dict[str, float]:
    flattened: Dict[str, float] = {}
    for group_key in ("executive_metrics", "risk_metrics", "pricing_metrics"):
        for metric in metric_groups.get(group_key, []):
            flattened[metric.metric_id] = float(metric.value)
    return flattened
