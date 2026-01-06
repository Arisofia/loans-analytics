from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import (KPICalculator, KPIMetadata, create_context)


class DefaultRateCalculator(KPICalculator):
    """Default Rate by loan count."""

    METADATA = KPIMetadata(
        name="DefaultRate",
        description="Percentage of loans in Default status",
        formula="count(loans WHERE status == 'Default') / count(total_loans) * 100",
        unit="%",
        data_sources=["loan_data"],
        owner="Risk",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        status_col = "loan_status" if "loan_status" in df.columns else "status"

        if status_col not in df.columns:
            raise ValueError(f"Missing column for DefaultRate: {status_col}")

        total_loans = len(df)
        default_loans = (df[status_col].astype(str).str.lower() == "default").sum()

        value = (default_loans / total_loans) * 100.0

        return float(value), create_context(
            self.METADATA.formula,
            rows_processed=total_loans,
            default_count=int(default_loans),
            status_column=status_col,
        )


def calculate_default_rate(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Default Rate calculation."""
    return DefaultRateCalculator().calculate(df)
