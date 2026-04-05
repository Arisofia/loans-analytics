from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

# Default thresholds from business rules
_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "par30": {"excellent": 2.0, "good": 5.0, "warning": 10.0, "critical": 20.0},
    "collection_rate": {"excellent": 95.0, "good": 90.0, "warning": 80.0, "critical": 70.0},
    "npl": {"excellent": 2.0, "good": 5.0, "warning": 8.0, "critical": 15.0},
    "cost_of_risk": {"excellent": 1.0, "good": 3.0, "warning": 6.0, "critical": 10.0},
    "default_rate": {"excellent": 1.0, "good": 2.0, "warning": 5.0, "critical": 10.0},
}

_WEIGHTS: Dict[str, float] = {
    "par30": 25.0,
    "collection_rate": 25.0,
    "npl": 20.0,
    "cost_of_risk": 15.0,
    "default_rate": 15.0,
}


def _score_lower_is_better(
    value: float, thresholds: Dict[str, float], weight: float
) -> tuple[float, str]:
    exc = thresholds["excellent"]
    good = thresholds["good"]
    warn = thresholds["warning"]
    crit = thresholds["critical"]

    if value <= exc:
        pts = weight
        status = "healthy"
    elif value <= good:
        pts = weight * 0.8
        status = "healthy"
    elif value <= warn:
        pts = weight * 0.55
        status = "at_risk"
    elif value <= crit:
        pts = weight * 0.25
        status = "warning"
    else:
        pts = 0.0
        status = "critical"
    return (round(pts, 2), status)


def _score_higher_is_better(
    value: float, thresholds: Dict[str, float], weight: float
) -> tuple[float, str]:
    exc = thresholds["excellent"]
    good = thresholds["good"]
    warn = thresholds["warning"]
    crit = thresholds["critical"]

    if value >= exc:
        pts = weight
        status = "healthy"
    elif value >= good:
        pts = weight * 0.8
        status = "healthy"
    elif value >= warn:
        pts = weight * 0.55
        status = "at_risk"
    elif value >= crit:
        pts = weight * 0.25
        status = "warning"
    else:
        pts = 0.0
        status = "critical"
    return (round(pts, 2), status)


def _traffic_light(score: float) -> str:
    if score >= 80:
        return "healthy"
    if score >= 60:
        return "at_risk"
    if score >= 40:
        return "warning"
    return "critical"


def compute_portfolio_health_score(
    par30: float,
    collection_rate: float,
    npl: float,
    cost_of_risk: float,
    default_rate: float,
) -> Dict[str, Any]:
    """Calculate aggregate portfolio health score (0-100)."""
    par30_pts, par30_status = _score_lower_is_better(par30, _THRESHOLDS["par30"], _WEIGHTS["par30"])
    cr_pts, cr_status = _score_higher_is_better(
        collection_rate, _THRESHOLDS["collection_rate"], _WEIGHTS["collection_rate"]
    )
    npl_pts, npl_status = _score_lower_is_better(npl, _THRESHOLDS["npl"], _WEIGHTS["npl"])
    cor_pts, cor_status = _score_lower_is_better(
        cost_of_risk, _THRESHOLDS["cost_of_risk"], _WEIGHTS["cost_of_risk"]
    )
    dr_pts, dr_status = _score_lower_is_better(
        default_rate, _THRESHOLDS["default_rate"], _WEIGHTS["default_rate"]
    )

    score = round(par30_pts + cr_pts + npl_pts + cor_pts + dr_pts, 2)
    light = _traffic_light(score)

    components = [
        {
            "dimension": "PAR30",
            "value": round(par30, 4),
            "points": par30_pts,
            "status": par30_status,
        },
        {
            "dimension": "Collection Rate",
            "value": round(collection_rate, 4),
            "points": cr_pts,
            "status": cr_status,
        },
        {
            "dimension": "NPL Ratio",
            "value": round(npl, 4),
            "points": npl_pts,
            "status": npl_status,
        },
        {
            "dimension": "Cost of Risk",
            "value": round(cost_of_risk, 4),
            "points": cor_pts,
            "status": cor_status,
        },
        {
            "dimension": "Default Rate",
            "value": round(default_rate, 4),
            "points": dr_pts,
            "status": dr_status,
        },
    ]

    critical_dims: list[str] = [
        str(c["dimension"]) for c in components if c["status"] == "critical"
    ]
    if critical_dims:
        interpretation = f"Critical condition. Action required on: {', '.join(critical_dims)}"
    elif any(c["status"] in ("at_risk", "warning") for c in components):
        interpretation = "Elevated risk. Monitor closely."
    else:
        interpretation = "Portfolio is healthy."

    return {
        "score": score,
        "rating": light,
        "components": components,
        "interpretation": interpretation,
    }


def compute_health_from_portfolio(portfolio_mart: pd.DataFrame) -> Dict[str, Any]:
    """Compute health score directly from a portfolio mart."""
    if portfolio_mart.empty:
        return compute_portfolio_health_score(0.0, 0.0, 0.0, 0.0, 0.0)

    from backend.src.kpi_engine.risk import (
        compute_npl_ratio,
        compute_par30,
        compute_default_rate_by_count,
    )
    from backend.src.kpi_engine.revenue import compute_collections_coverage

    # In practice cost_of_risk calculation would be here or in unit_economics

    par30 = float(compute_par30(portfolio_mart)) * 100.0
    npl = float(compute_npl_ratio(portfolio_mart)) * 100.0
    dr = float(compute_default_rate_by_count(portfolio_mart)) * 100.0
    coll = float(compute_collections_coverage(portfolio_mart))

    # Fallback for Cost of Risk if not fully implemented in canonical engine yet
    cor = 0.0

    return compute_portfolio_health_score(
        par30=par30, collection_rate=coll, npl=npl, cost_of_risk=cor, default_rate=dr
    )
