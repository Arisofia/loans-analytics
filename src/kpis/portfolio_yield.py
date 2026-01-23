from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import (KPICalculator, KPIMetadata, create_context,
                           safe_numeric)


class PortfolioYieldCalculator(KPICalculator):
    """Weighted Average Portfolio Yield."""

    METADATA = KPIMetadata(
        name="PortfolioYield",
        description="Weighted average interest rate across the portfolio",
        formula="SUM(interest_rate * principal_balance) / SUM(principal_balance) * 100",
        unit="%",
        data_sources=["loan_data"],
        threshold_warning=8.0,
        threshold_critical=6.0,
        owner="Finance",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        required = ["interest_rate", "principal_balance"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        interest_rate = safe_numeric(df["interest_rate"])
        principal_balance = safe_numeric(df["principal_balance"])

        total_principal = principal_balance.sum()
        if total_principal == 0:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=len(df), reason="Zero total principal"
            )

        weighted_interest = (interest_rate * principal_balance).sum()
        yield_val = (weighted_interest / total_principal) * 100.0

        return yield_val, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            total_principal=float(total_principal),
            weighted_interest=float(weighted_interest),
        )


def calculate_portfolio_yield(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Portfolio Yield calculation."""
    return PortfolioYieldCalculator().calculate(df)
