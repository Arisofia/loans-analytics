from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context


class ActiveClientsCalculator(KPICalculator):
    """Number of Unique Active Clients."""

    METADATA = KPIMetadata(
        name="ActiveClients",
        description="Count of unique customers with active (Current) loans",
        formula="COUNT(DISTINCT customer_id WHERE loan_status == 'Current')",
        unit="count",
        data_sources=["loan_data"],
        owner="Growth",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        status_col = "loan_status" if "loan_status" in df.columns else "status"
        cust_col = "customer_id" if "customer_id" in df.columns else "Customer ID"

        if status_col not in df.columns or cust_col not in df.columns:
            if "customer_id" not in df.columns:
                cust_col = "client_id"

        if status_col not in df.columns or cust_col not in df.columns:
            raise ValueError(
                f"Missing columns for ActiveClients: {status_col}, {cust_col}"
            )

        active_mask = df[status_col].astype(str).str.lower() == "current"
        active_clients = df[active_mask][cust_col].nunique()

        return float(active_clients), create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            active_loans_count=int(active_mask.sum()),
            status_column=status_col,
            customer_column=cust_col,
        )


def calculate_active_clients(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Active Clients calculation."""
    return ActiveClientsCalculator().calculate(df)
