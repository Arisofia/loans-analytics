from __future__ import annotations

import pandas as pd

from backend.src.kpi_engine.concentration import compute_hhi


def test_hhi_formula_known_distribution() -> None:
    """Validate HHI = sum(share^2) * 10000 using a deterministic sample."""
    portfolio = pd.DataFrame(
        {
            "borrower_id": ["A", "B", "C"],
            "current_balance": [50, 30, 20],
        }
    )

    result = compute_hhi(portfolio)

    # Shares = 0.5, 0.3, 0.2 -> HHI = (0.25 + 0.09 + 0.04) * 10000 = 3800
    assert result["hhi_index"] == 3800.0
    assert result["concentration_level"] == "high"


def test_hhi_zero_total_returns_unknown() -> None:
    portfolio = pd.DataFrame(
        {
            "borrower_id": ["A", "B"],
            "current_balance": [0, 0],
        }
    )

    result = compute_hhi(portfolio)

    assert result["hhi_index"] == 0.0
    assert result["concentration_level"] == "unknown"
