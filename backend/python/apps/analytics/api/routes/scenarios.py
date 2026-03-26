"""Scenario engine routes — base / downside / stress cases."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/scenarios", tags=["scenarios"])


class ScenarioRequest(BaseModel):
    current_metrics: Dict[str, Any] = Field(
        ..., description="Current portfolio/financial metrics."
    )


class ScenarioResult(BaseModel):
    scenario: str
    projected_metrics: Dict[str, Any] = Field(default_factory=dict)
    triggers: List[str] = Field(default_factory=list)
    narrative: str = ""


class ScenarioCompareResponse(BaseModel):
    results: List[ScenarioResult]
    count: int


@router.post("/base", response_model=ScenarioResult)
async def run_base_case(req: ScenarioRequest):
    """Run the base-case scenario."""
    try:
        from backend.src.scenario_engine.base_case import run as run_base

        result = run_base(req.current_metrics)
        return ScenarioResult(
            scenario="base",
            projected_metrics=result.get("projected_metrics", {}),
            triggers=result.get("triggers", []),
            narrative=result.get("narrative", ""),
        )
    except Exception as exc:
        logger.error("Base case error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/downside", response_model=ScenarioResult)
async def run_downside_case(req: ScenarioRequest):
    """Run the downside scenario."""
    try:
        from backend.src.scenario_engine.downside_case import run as run_down

        result = run_down(req.current_metrics)
        return ScenarioResult(
            scenario="downside",
            projected_metrics=result.get("projected_metrics", {}),
            triggers=result.get("triggers", []),
            narrative=result.get("narrative", ""),
        )
    except Exception as exc:
        logger.error("Downside case error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/stress", response_model=ScenarioResult)
async def run_stress_case(req: ScenarioRequest):
    """Run the stress-test scenario."""
    try:
        from backend.src.scenario_engine.stress_case import run as run_stress

        result = run_stress(req.current_metrics)
        return ScenarioResult(
            scenario="stress",
            projected_metrics=result.get("projected_metrics", {}),
            triggers=result.get("triggers", []),
            narrative=result.get("narrative", ""),
        )
    except Exception as exc:
        logger.error("Stress case error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/compare", response_model=ScenarioCompareResponse)
async def compare_all(req: ScenarioRequest):
    """Run all three scenarios and return a comparison."""
    results: List[ScenarioResult] = []
    for runner_name, label in [
        ("base_case", "base"),
        ("downside_case", "downside"),
        ("stress_case", "stress"),
    ]:
        try:
            import importlib

            mod = importlib.import_module(
                f"backend.src.scenario_engine.{runner_name}"
            )
            out = mod.run(req.current_metrics)
            results.append(
                ScenarioResult(
                    scenario=label,
                    projected_metrics=out.get("projected_metrics", {}),
                    triggers=out.get("triggers", []),
                    narrative=out.get("narrative", ""),
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scenario %s failed: %s", label, exc)
            results.append(
                ScenarioResult(scenario=label, narrative=f"Error: {exc}")
            )
    return ScenarioCompareResponse(results=results, count=len(results))
