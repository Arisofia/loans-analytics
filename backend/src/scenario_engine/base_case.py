"""Base-case scenario — status-quo projection with no shocks.

Growth and risk metrics continue at current trajectory.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.src.scenario_engine.assumptions import get_horizon, get_multipliers
from backend.src.scenario_engine.engine import ScenarioResult, _d

SCENARIO_NAME = "base"


def run(current_metrics: Dict[str, Any]) -> ScenarioResult:
    """Project metrics under base-case assumptions."""
    multipliers = get_multipliers(SCENARIO_NAME)
    horizon = get_horizon(SCENARIO_NAME)

    projected: Dict[str, Any] = {}
    triggers: list[str] = []

    for metric_id, value in current_metrics.items():
        if value is None:
            projected[metric_id] = None
            continue
        mult = multipliers.get(metric_id, 1.0)
        projected[metric_id] = float((_d(value) * _d(mult)).quantize(_d("0.0001")))

    return ScenarioResult(
        name=SCENARIO_NAME,
        horizon_months=horizon,
        projected_metrics=projected,
        triggers=triggers,
    )
