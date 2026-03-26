"""KPI engine entrypoint — single ``run_metric_engine`` facade.

Calls every KPI module (risk, revenue, liquidity, concentration,
unit_economics, cohorts, capital, covenants) and returns a flat dict
of all computed metric values keyed by metric_id.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import pandas as pd

from backend.src.kpi_engine import (
    capital,
    cohorts,
    concentration,
    covenants,
    liquidity,
    revenue,
    risk,
    unit_economics,
)

logger = logging.getLogger(__name__)


def run_metric_engine(
    marts: Dict[str, pd.DataFrame],
    *,
    equity: Optional[Decimal] = None,
    lgd: Decimal = Decimal("0.10"),
    min_collection_rate: float = 98.5,
) -> Dict[str, Any]:
    """Execute the full KPI engine over the mart bundle.

    Parameters
    ----------
    marts : dict
        Keyed by mart name (``portfolio_mart``, ``finance_mart``, etc.).
    equity : Decimal, optional
        Explicit total equity for capital computations.
    lgd : Decimal
        Loss-given-default for expected-loss calculation.
    min_collection_rate : float
        Threshold for liquidity warning.

    Returns
    -------
    dict
        Flat dict ``{metric_id: value}`` with all computed metrics.
    """
    portfolio = marts.get("portfolio_mart", pd.DataFrame())
    finance = marts.get("finance_mart", pd.DataFrame())
    treasury = marts.get("treasury_mart", pd.DataFrame())
    collections = marts.get("collections_mart", pd.DataFrame())

    results: Dict[str, Any] = {}

    # ── Risk module ──────────────────────────────────────────────────────
    if not portfolio.empty:
        results.update(risk.compute_par(portfolio))
        results.update(risk.compute_npl(portfolio))
        results.update(risk.compute_default_rate(portfolio))
        results.update(risk.compute_expected_loss(portfolio, lgd))

    # ── Revenue module ───────────────────────────────────────────────────
    if not finance.empty:
        results.update(revenue.compute_revenue_metrics(finance))

    # ── Liquidity module ─────────────────────────────────────────────────
    if not treasury.empty:
        results.update(liquidity.compute_liquidity_metrics(treasury))

    # ── Concentration module ─────────────────────────────────────────────
    if not portfolio.empty:
        results.update(concentration.compute_concentration_metrics(portfolio))

    # ── Unit economics module ────────────────────────────────────────────
    if not finance.empty:
        results.update(unit_economics.compute_unit_economics(finance))

    # ── Cohort module ────────────────────────────────────────────────────
    if not portfolio.empty:
        cohort_data = cohorts.compute_vintage_analysis(portfolio)
        results["vintage_cohorts"] = cohort_data

    # ── Capital module ───────────────────────────────────────────────────
    if not finance.empty and not treasury.empty:
        results.update(capital.compute_capital_metrics(finance, treasury, equity=equity))

    # ── Covenants module ─────────────────────────────────────────────────
    if not portfolio.empty:
        _equity = equity if equity is not None else Decimal("0")
        covenant_result = covenants.check_all_covenants(portfolio, equity=_equity)
        results["covenant_status"] = covenant_result["covenant_status"]
        results["covenant_breaches"] = covenant_result["breaches"]
        results["eligible_portfolio_ratio"] = covenant_result["eligible_portfolio"].get(
            "eligible_portfolio_ratio", 0.0
        )

    logger.info("KPI engine computed %d metrics", len(results))
    return results
