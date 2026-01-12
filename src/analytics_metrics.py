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


__all__ = [
    "calculate_quality_score",
    "portfolio_kpis",
    "project_growth",
    "standardize_numeric",
]
