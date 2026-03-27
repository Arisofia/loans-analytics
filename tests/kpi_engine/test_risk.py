"""Tests for backend.src.kpi_engine.risk — first live slice."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.src.kpi_engine.risk import (
    compute_expected_loss,
    compute_par30,
)


@pytest.fixture()
def portfolio_mart() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3", "L4"],
            "days_past_due": [0, 15, 35, 95],
            "outstanding_principal": [1000.0, 2000.0, 3000.0, 4000.0],
            "dpd_bucket": ["current", "1_30", "31_60", "90_plus"],
        }
    )


def test_par30_basic(portfolio_mart: pd.DataFrame) -> None:
    result = compute_par30(portfolio_mart)
    # dpd>=30: L3(3000)+L4(4000)=7000, total=10000 → 0.70
    assert result == pytest.approx(0.70)


def test_par30_empty() -> None:
    df = pd.DataFrame(columns=["loan_id", "days_past_due"])
    assert compute_par30(df) == 0.0


def test_expected_loss_defaults(portfolio_mart: pd.DataFrame) -> None:
    el = compute_expected_loss(portfolio_mart)
    assert el > 0.0
    # pd=0.03, lgd=0.45, ead=sum(outstanding_principal)=10_000
    expected = 0.03 * 0.45 * 10_000.0
    assert el == pytest.approx(expected)


def test_expected_loss_with_scorecard(portfolio_mart: pd.DataFrame) -> None:
    scorecard_df = pd.DataFrame({
        "loan_id": ["L1", "L2", "L3", "L4"],
        "pd": [0.05, 0.10, 0.20, 0.30],
        "lgd": [0.40, 0.40, 0.50, 0.60],
    })
    el = compute_expected_loss(portfolio_mart, scorecard_df=scorecard_df)
    # L1: 0.05*0.40*1000, L2: 0.10*0.40*2000, L3: 0.20*0.50*3000, L4: 0.30*0.60*4000
    expected = (0.05 * 0.40 * 1000) + (0.10 * 0.40 * 2000) + (0.20 * 0.50 * 3000) + (0.30 * 0.60 * 4000)
    assert el == pytest.approx(expected)
