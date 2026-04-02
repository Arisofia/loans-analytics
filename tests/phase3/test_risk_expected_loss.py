from __future__ import annotations

from decimal import Decimal

import pandas as pd

from backend.src.kpi_engine.risk import compute_expected_loss, compute_lgd


def test_compute_lgd_empirical_with_bounds() -> None:
    lgd = compute_lgd(
        total_disbursed=Decimal("1000"),
        total_recovered=Decimal("800"),
        method="empirical",
        fixed_rate=Decimal("0.9"),
        floor=Decimal("0.40"),
        ceil=Decimal("0.95"),
    )
    # Raw LGD would be 0.2, but floor enforces 0.4
    assert lgd == Decimal("0.4000")


def test_expected_loss_uses_pd_source_and_empirical_lgd() -> None:
    portfolio = pd.DataFrame(
        {
            "loan_id": ["L1", "L2"],
            "days_past_due": [0, 180],
            "status": ["current", "defaulted"],
            "outstanding_principal": [1000, 500],
            "principal_amount": [1000, 500],
            "recovery_amount": [400, 200],
            "pd_scorecard": [0.10, 0.40],
        }
    )

    business_params = {
        "financial_assumptions": {
            "lgd_method": "empirical",
            "lgd_fixed_rate": 0.90,
            "lgd_floor": 0.40,
            "lgd_ceil": 0.95,
        },
        "pd_assignment": {
            "source": "scorecard",
            "dpd_buckets": {
                "current": 0.005,
                "dpd_30": 0.050,
                "dpd_60": 0.150,
                "dpd_90": 0.350,
                "dpd_180": 0.700,
                "defaulted": 1.000,
            },
        },
    }

    # total_recovered / total_disbursed = 600/1500 = 0.4 -> lgd = 0.6
    # EL = (0.10*0.6*1000) + (0.40*0.6*500) = 60 + 120 = 180
    el = compute_expected_loss(portfolio, business_params=business_params)

    assert el == 180.0
