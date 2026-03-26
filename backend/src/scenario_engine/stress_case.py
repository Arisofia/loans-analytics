"""Stress-case scenario — severe adverse conditions.

Models a systemic shock with significantly higher defaults, sharp
drop in origination, and liquidity crunch.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.src.scenario_engine.assumptions import get_horizon, get_multipliers
from backend.src.scenario_engine.engine import ScenarioResult, _d

SCENARIO_NAME = "stress"

_RISK_METRICS = {"par_30", "par_60", "par_90", "npl_ratio", "default_rate"}


def run(current_metrics: Dict[str, Any]) -> ScenarioResult:
    """Project metrics under stress assumptions."""
    multipliers = get_multipliers(SCENARIO_NAME)
    horizon = get_horizon(SCENARIO_NAME)

    projected: Dict[str, Any] = {}
    triggers: List[str] = []

    for metric_id, value in current_metrics.items():
        if value is None:
            projected[metric_id] = None
            continue
        mult = multipliers.get(metric_id, 1.0)
        projected[metric_id] = float((_d(value) * _d(mult)).quantize(_d("0.0001")))

        if metric_id in _RISK_METRICS and mult > 1.0:
            triggers.append(f"{metric_id} projected to rise {(mult - 1) * 100:.0f}% under stress")
        if metric_id == "liquidity_ratio" and mult < 1.0:
            triggers.append(f"liquidity projected to contract {(1 - mult) * 100:.0f}% under stress")

    return ScenarioResult(
        name=SCENARIO_NAME,
        horizon_months=horizon,
        projected_metrics=projected,
        triggers=triggers,
    )
