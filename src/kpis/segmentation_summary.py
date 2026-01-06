from typing import Any, Dict, List, Tuple

import pandas as pd

from src.kpis.base import (KPICalculator, KPIMetadata, create_context,
                           safe_numeric)


class SegmentationSummaryCalculator(KPICalculator):
    """Client Segment KPI Summary Analysis."""

    METADATA = KPIMetadata(
        name="SegmentationSummary",
        description="KPI summary aggregated by Client Segment (2025)",
        formula="GROUP BY Client Segment AGG(nunique(Customer ID), sum(Outstanding), mean(Approved))",
        unit="mixed",
        data_sources=["loan_data", "customer_data", "payment_data"],
        owner="Commercial",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate segmentation summary.
        Note: This is a complex KPI that returns a summary table in the context.
        The float return value is the total active clients count as a primary metric.
        """
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        # Standardize column names (mapping from user request to common internal names)
        # User: 'Origination Date', 'Customer ID', 'Client Segment', 'Outstanding Amount', 'Approved Amount'
        col_map = {
            "Origination Date": "origination_date",
            "Customer ID": "customer_id",
            "Client Segment": "client_segment",
            "Outstanding Amount": "outstanding_amount",
            "Approved Amount": "approved_amount",
            "Payment Date": "payment_date",
            "Days Past Due": "days_past_due",
        }

        working_df = df.copy()
        for old_col, new_col in col_map.items():
            if old_col in working_df.columns:
                working_df[new_col] = working_df[old_col]

        # Ensure datetime for filtering
        date_col = (
            "origination_date" if "origination_date" in working_df.columns else "Origination Date"
        )
        if date_col in working_df.columns:
            working_df[date_col] = pd.to_datetime(working_df[date_col], errors="coerce")
            # Prepare 2025 filtered dataset
            df_2025 = working_df[working_df[date_col].dt.year == 2025].copy()
        else:
            df_2025 = working_df.copy()

        if df_2025.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=len(df), reason="No data for 2025"
            )

        # Required columns check
        segment_col = "client_segment" if "client_segment" in df_2025.columns else "Client Segment"
        cust_col = "customer_id" if "customer_id" in df_2025.columns else "Customer ID"
        outstanding_col = (
            "outstanding_amount"
            if "outstanding_amount" in df_2025.columns
            else "Outstanding Amount"
        )
        approved_col = (
            "approved_amount" if "approved_amount" in df_2025.columns else "Approved Amount"
        )

        if segment_col not in df_2025.columns:
            # Default to 'Unsegmented' if missing
            df_2025[segment_col] = "Unsegmented"

        # KPIs per segment
        summary = (
            df_2025.groupby(segment_col)
            .agg(
                Clients=(cust_col, "nunique"),
                Portfolio_Value=(outstanding_col, "sum"),
                Avg_Loan=(approved_col, "mean"),
            )
            .reset_index()
        )

        # Join with delinquency if present
        dpd_col = "days_past_due" if "days_past_due" in df_2025.columns else "Days Past Due"
        if dpd_col in df_2025.columns:
            delinquent = df_2025[safe_numeric(df_2025[dpd_col]) > 30]
            delinquency_counts = delinquent.groupby(segment_col).size()

            # Map back to summary
            total_clients = summary.set_index(segment_col)["Clients"]
            delinquency_rate = (delinquency_counts / total_clients).fillna(0).round(3) * 100
            summary["Delinquency_Rate"] = summary[segment_col].map(delinquency_rate).fillna(0)

        # Main metric: Total Clients 2025
        total_active_clients = float(df_2025[cust_col].nunique())

        return total_active_clients, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            segmentation_data=summary.to_dict(orient="records"),
            total_2025_clients=total_active_clients,
        )


def calculate_segmentation_summary(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Segmentation Summary calculation."""
    return SegmentationSummaryCalculator().calculate(df)
