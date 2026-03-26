"""Tests for DataQualityAgent — first live slice."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.python.multi_agent.agents.data_quality_agent import DataQualityAgent


@pytest.fixture()
def clean_loans() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3"],
            "customer_id": ["C1", "C2", "C3"],
            "days_past_due": [0, 10, 25],
            "outstanding_principal": [1000.0, 2000.0, 3000.0],
        }
    )


@pytest.fixture()
def dirty_loans() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L1", None, "L1"],
            "customer_id": ["C1", "C2", "C3"],
            "days_past_due": [0, -5, 25],
            "outstanding_principal": [1000.0, 2000.0, 3000.0],
        }
    )


def test_clean_data_no_blocking(clean_loans: pd.DataFrame) -> None:
    agent = DataQualityAgent()
    output = agent.run(
        marts={"portfolio_mart": clean_loans},
        metrics=[],
        features={},
        quality={"quality_score": 1.0, "blocking_issues": [], "warnings": []},
    )
    assert output.status == "ok"
    assert output.blocked_by == []


def test_dirty_data_blocked(dirty_loans: pd.DataFrame) -> None:
    agent = DataQualityAgent()
    output = agent.run(
        marts={"portfolio_mart": dirty_loans},
        metrics=[],
        features={},
        quality={},
    )
    assert output.status == "blocked"
    assert "data_quality" in output.blocked_by
    assert len(output.alerts) > 0
