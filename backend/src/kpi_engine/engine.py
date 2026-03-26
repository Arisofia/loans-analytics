from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from backend.src.contracts.metric_schema import MetricResult
from backend.src.kpi_engine import cohorts, revenue, risk, unit_economics


def _mr(metric_id: str, name: str, value: float, unit: str, mart: str, owner: str) -> MetricResult:
    return MetricResult(
        metric_id=metric_id,
        metric_name=name,
        value=value,
        unit=unit,
        as_of_date=date.today(),
        source_mart=mart,
        owner=owner,
    )


def run_metric_engine(
    marts: dict[str, pd.DataFrame],
    quality_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    portfolio = marts.get("portfolio_mart", pd.DataFrame())
    finance = marts.get("finance_mart", pd.DataFrame())
    sales = marts.get("sales_mart", pd.DataFrame())

    executive: list[MetricResult] = []
    risk_metrics: list[MetricResult] = []
    pricing: list[MetricResult] = []

    # Risk
    risk_metrics.append(_mr("par30", "PAR 30", risk.compute_par30(portfolio), "ratio", "portfolio", "risk"))
    risk_metrics.append(_mr("par60", "PAR 60", risk.compute_par60(portfolio), "ratio", "portfolio", "risk"))
    risk_metrics.append(_mr("par90", "PAR 90", risk.compute_par90(portfolio), "ratio", "portfolio", "risk"))
    risk_metrics.append(_mr("expected_loss", "Expected Loss", risk.compute_expected_loss(portfolio), "currency", "portfolio", "risk"))

    # Revenue / pricing
    pricing.append(_mr("net_yield", "Net Yield", revenue.compute_net_yield(finance), "ratio", "finance", "cfo"))
    pricing.append(_mr("spread", "Spread", revenue.compute_spread(finance), "ratio", "finance", "cfo"))

    # Unit economics → executive
    executive.append(_mr("avg_ticket", "Avg Ticket", unit_economics.compute_avg_ticket(sales), "currency", "sales", "commercial"))
    executive.append(_mr("win_rate", "Win Rate", unit_economics.compute_win_rate(sales), "ratio", "sales", "commercial"))
    executive.append(_mr("contribution_margin", "Contribution Margin", unit_economics.compute_contribution_margin(finance), "currency", "finance", "cfo"))

    # Cohorts
    cohort_curve = cohorts.build_cohort_default_curve(portfolio)
    vintage_summary = cohorts.build_vintage_quality_summary(portfolio)

    return {
        "executive_metrics": executive,
        "risk_metrics": risk_metrics,
        "pricing_metrics": pricing,
        "cohort_outputs": {
            "default_curve": cohort_curve,
            "vintage_summary": vintage_summary,
        },
    }
        results["eligible_portfolio_ratio"] = covenant_result["eligible_portfolio"].get(
            "eligible_portfolio_ratio", 0.0
        )

    logger.info("KPI engine computed %d metrics", len(results))
    return results
