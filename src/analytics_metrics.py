import json
import logging
from pathlib import Path
from typing import Any, Dict, List

# Re-exporting real implementations from src/analytics package
from src.analytics import (calculate_quality_score, portfolio_kpis,
                           project_growth, standardize_numeric)

ROOT = tuple(Path(__file__).resolve().parents)[1]
DASHBOARD_JSON = ROOT / "exports" / "complete_kpi_dashboard.json"

logger = logging.getLogger(__name__)


def load_dashboard_metrics() -> Dict[str, Any]:
    """Load computed KPI dashboard from JSON."""
    if not DASHBOARD_JSON.exists():
        return {}
    try:
        with DASHBOARD_JSON.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.error("Expected dict in %s, got %s", DASHBOARD_JSON, type(data).__name__)
            return {}
        return data
    except json.JSONDecodeError as e:
        logger.error("Failed to parse dashboard metrics %s: %s", DASHBOARD_JSON, e)
        return {}
    except OSError as e:
        logger.error("Failed to read dashboard metrics %s: %s", DASHBOARD_JSON, e)
        return {}


def get_portfolio_fundamentals() -> Dict[str, Any]:
    """Get portfolio fundamentals from dashboard."""
    data = load_dashboard_metrics()
    return data.get("portfolio_fundamentals", {})


def get_growth_metrics() -> Dict[str, Any]:
    """Get growth metrics from dashboard."""
    data = load_dashboard_metrics()
    return data.get("growth_metrics", {})


def get_monthly_pricing() -> List[Dict[str, Any]]:
    """Get monthly pricing from dashboard."""
    data = load_dashboard_metrics()
    return data.get("extended_kpis", {}).get("monthly_pricing", [])


def get_monthly_risk() -> List[Dict[str, Any]]:
    """Get monthly risk from dashboard."""
    data = load_dashboard_metrics()
    return data.get("extended_kpis", {}).get("monthly_risk", [])


def get_customer_types() -> List[Dict[str, Any]]:
    """Get customer types from dashboard."""
    data = load_dashboard_metrics()
    return data.get("extended_kpis", {}).get("customer_types", [])


__all__ = [
    "calculate_quality_score",
    "portfolio_kpis",
    "project_growth",
    "standardize_numeric",
    "load_dashboard_metrics",
    "get_portfolio_fundamentals",
    "get_growth_metrics",
    "get_monthly_pricing",
    "get_monthly_risk",
    "get_customer_types",
]
