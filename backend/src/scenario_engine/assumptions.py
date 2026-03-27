"""Scenario assumptions — loads and validates YAML-driven scenario parameters.

Centralises assumption management for all scenario modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "scenarios" / "scenario_assumptions.yaml"


def load_assumptions(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load scenario assumptions from YAML, falling back to built-in defaults."""
    path = Path(config_path) if config_path else _DEFAULT_CONFIG
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return _builtin_defaults()


def get_scenario(name: str, config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return the assumptions block for a single scenario name."""
    cfg = load_assumptions(config_path)
    return cfg.get("scenarios", {}).get(name, {})


def get_multipliers(name: str, config_path: Optional[Path] = None) -> Dict[str, float]:
    """Return multipliers dict for a scenario."""
    return get_scenario(name, config_path).get("multipliers", {})


def get_horizon(name: str, config_path: Optional[Path] = None) -> int:
    """Return projection horizon in months."""
    return get_scenario(name, config_path).get("horizon_months", 12)


def _builtin_defaults() -> Dict[str, Any]:
    return {
        "scenarios": {
            "base": {
                "horizon_months": 12,
                "multipliers": {
                    "par_30": 1.0, "par_60": 1.0, "par_90": 1.0,
                    "npl_ratio": 1.0, "default_rate": 1.0, "expected_loss": 1.0,
                    "total_outstanding_balance": 1.10,
                    "disbursement_volume_mtd": 1.10,
                    "liquidity_ratio": 1.0, "collection_rate": 1.0,
                },
            },
            "downside": {
                "horizon_months": 12,
                "multipliers": {
                    "par_30": 1.25, "par_60": 1.30, "par_90": 1.35,
                    "npl_ratio": 1.30, "default_rate": 1.30, "expected_loss": 1.35,
                    "total_outstanding_balance": 0.95,
                    "disbursement_volume_mtd": 0.85,
                    "liquidity_ratio": 0.90, "collection_rate": 0.97,
                },
            },
            "stress": {
                "horizon_months": 12,
                "multipliers": {
                    "par_30": 1.60, "par_60": 1.80, "par_90": 2.00,
                    "npl_ratio": 1.80, "default_rate": 1.80, "expected_loss": 2.00,
                    "total_outstanding_balance": 0.80,
                    "disbursement_volume_mtd": 0.60,
                    "liquidity_ratio": 0.75, "collection_rate": 0.92,
                },
            },
        }
    }
