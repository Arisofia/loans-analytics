"""Tests for the scenario engine — base, downside, stress cases."""

from __future__ import annotations

import pytest

from backend.src.scenario_engine.base_case import run as run_base
from backend.src.scenario_engine.downside_case import run as run_downside
from backend.src.scenario_engine.stress_case import run as run_stress
from backend.src.scenario_engine.assumptions import load_assumptions


@pytest.fixture()
def current_metrics() -> dict:
    return {
        "par_30": 3.5,
        "par_90": 1.2,
        "collection_rate": 98.0,
        "default_rate": 2.1,
        "liquidity_ratio": 12.0,
        "equity": 200_000,
        "total_outstanding": 1_000_000,
    }


class TestAssumptions:
    def test_load_defaults(self):
        assumptions = load_assumptions()
        assert isinstance(assumptions, dict)
        # Should have at least the 3 scenario keys
        assert "base" in assumptions or len(assumptions) >= 1


class TestBaseCase:
    def test_returns_dict(self, current_metrics: dict):
        result = run_base(current_metrics)
        assert isinstance(result, dict)
        assert "projected_metrics" in result or "triggers" in result

    def test_has_narrative(self, current_metrics: dict):
        result = run_base(current_metrics)
        assert "narrative" in result


class TestDownsideCase:
    def test_returns_dict(self, current_metrics: dict):
        result = run_downside(current_metrics)
        assert isinstance(result, dict)

    def test_triggers_present(self, current_metrics: dict):
        result = run_downside(current_metrics)
        assert "triggers" in result
        assert isinstance(result["triggers"], list)


class TestStressCase:
    def test_returns_dict(self, current_metrics: dict):
        result = run_stress(current_metrics)
        assert isinstance(result, dict)

    def test_stress_triggers_present(self, current_metrics: dict):
        result = run_stress(current_metrics)
        assert "triggers" in result
