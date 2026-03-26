"""Scenario engine — project base / downside / stress from real portfolio metrics.

All projections start from actual KPI values and apply multipliers; no
fabricated data.  Scenario assumptions live in
``config/scenarios/scenario_assumptions.yaml``.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "scenarios" / "scenario_assumptions.yaml"


# ── helpers ──────────────────────────────────────────────────────────────
def _d(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


# ── scenario result data class ──────────────────────────────────────────
class ScenarioResult:
    """Container for one scenario's projections."""

    __slots__ = ("name", "horizon_months", "projected_metrics", "triggers", "generated_at")

    def __init__(
        self,
        name: str,
        horizon_months: int,
        projected_metrics: Dict[str, Any],
        triggers: List[str],
    ):
        self.name = name
        self.horizon_months = horizon_months
        self.projected_metrics = projected_metrics
        self.triggers = triggers
        self.generated_at = dt.datetime.now(dt.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.name,
            "horizon_months": self.horizon_months,
            "projected": self.projected_metrics,
            "triggers": self.triggers,
            "generated_at": self.generated_at,
        }


# ── engine ───────────────────────────────────────────────────────────────
class ScenarioEngine:
    """Project portfolio metrics under base / downside / stress assumptions.

    Parameters
    ----------
    config_path : Path | str | None
        YAML file with scenario multipliers.  Falls back to built-in
        defaults when the file does not exist.
    """

    def __init__(self, config_path: Optional[Path] = None):
        cfg_path = Path(config_path) if config_path else _DEFAULT_CONFIG
        if cfg_path.exists():
            with open(cfg_path, encoding="utf-8") as fh:
                self._cfg: Dict[str, Any] = yaml.safe_load(fh) or {}
        else:
            self._cfg = self._builtin_defaults()

    # ── public API ───────────────────────────────────────────────────────
    def run_all(self, current_metrics: Dict[str, Any]) -> List[ScenarioResult]:
        """Run base, downside, and stress scenarios."""
        return [
            self._project("base", current_metrics),
            self._project("downside", current_metrics),
            self._project("stress", current_metrics),
        ]

    def run_scenario(self, name: str, current_metrics: Dict[str, Any]) -> ScenarioResult:
        """Run a single named scenario."""
        return self._project(name, current_metrics)

    # ── projection logic ─────────────────────────────────────────────────
    def _project(self, scenario_name: str, current: Dict[str, Any]) -> ScenarioResult:
        assumptions = self._cfg.get("scenarios", {}).get(scenario_name, {})
        horizon = assumptions.get("horizon_months", 12)
        multipliers: Dict[str, float] = assumptions.get("multipliers", {})
        triggers: List[str] = []

        projected: Dict[str, Any] = {}
        for metric_id, value in current.items():
            if value is None:
                projected[metric_id] = None
                continue
            mult = multipliers.get(metric_id, 1.0)
            proj_val = _d(value) * _d(mult)
            projected[metric_id] = float(proj_val.quantize(Decimal("0.0001")))

            # Trigger detection
            if metric_id in ("par_30", "par_60", "par_90", "npl_ratio", "default_rate"):
                if mult > 1.0:
                    triggers.append(f"{metric_id} projected to rise {(mult - 1) * 100:.0f}%")
            if metric_id == "liquidity_ratio" and mult < 1.0:
                triggers.append(f"liquidity projected to contract {(1 - mult) * 100:.0f}%")

        return ScenarioResult(
            name=scenario_name,
            horizon_months=horizon,
            projected_metrics=projected,
            triggers=triggers,
        )

    # ── fallback defaults ────────────────────────────────────────────────
    @staticmethod
    def _builtin_defaults() -> Dict[str, Any]:
        return {
            "scenarios": {
                "base": {
                    "horizon_months": 12,
                    "multipliers": {
                        "par_30": 1.0,
                        "par_60": 1.0,
                        "par_90": 1.0,
                        "npl_ratio": 1.0,
                        "default_rate": 1.0,
                        "expected_loss": 1.0,
                        "total_outstanding_balance": 1.10,
                        "disbursement_volume_mtd": 1.10,
                        "liquidity_ratio": 1.0,
                        "collection_rate": 1.0,
                    },
                },
                "downside": {
                    "horizon_months": 12,
                    "multipliers": {
                        "par_30": 1.25,
                        "par_60": 1.30,
                        "par_90": 1.35,
                        "npl_ratio": 1.30,
                        "default_rate": 1.30,
                        "expected_loss": 1.35,
                        "total_outstanding_balance": 0.95,
                        "disbursement_volume_mtd": 0.85,
                        "liquidity_ratio": 0.90,
                        "collection_rate": 0.97,
                    },
                },
                "stress": {
                    "horizon_months": 6,
                    "multipliers": {
                        "par_30": 1.60,
                        "par_60": 1.80,
                        "par_90": 2.00,
                        "npl_ratio": 1.80,
                        "default_rate": 1.80,
                        "expected_loss": 2.00,
                        "total_outstanding_balance": 0.85,
                        "disbursement_volume_mtd": 0.60,
                        "liquidity_ratio": 0.75,
                        "collection_rate": 0.93,
                    },
                },
            }
        }
