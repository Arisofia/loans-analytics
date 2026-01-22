import logging
from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.data_normalization import (COL_APPROVED_AMOUNT,
                                          COL_CLIENT_SEGMENT, COL_CUSTOMER_ID,
                                          COL_DAYS_PAST_DUE,
                                          COL_ORIGINATION_DATE,
                                          COL_OUTSTANDING_AMOUNT,
                                          normalize_columns)
from src.utils.numeric import safe_numeric

logger = logging.getLogger(__name__)


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

        # Standardize column names
        working_df = normalize_columns(df)

        # Ensure datetime for filtering
        if COL_ORIGINATION_DATE in working_df.columns:
            working_df[COL_ORIGINATION_DATE] = pd.to_datetime(
                working_df[COL_ORIGINATION_DATE], errors="coerce"
            )
            # Prepare 2025 filtered dataset
            df_2025 = working_df[
                working_df[COL_ORIGINATION_DATE].dt.year == 2025
            ].copy()
            if df_2025.empty:
                logger.warning(
                    "No data found for year 2025 in column %s", COL_ORIGINATION_DATE
                )
                # Fallback to all data if 2025 filter yields nothing but date col exists
                df_2025 = working_df.copy()
        else:
            df_2025 = working_df.copy()

        if df_2025.empty:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                reason="DataFrame empty after preprocessing",
            )

        # Required columns check with defaults
        if COL_CLIENT_SEGMENT not in df_2025.columns:
            df_2025[COL_CLIENT_SEGMENT] = "Unsegmented"

        if COL_CUSTOMER_ID not in df_2025.columns:
            df_2025[COL_CUSTOMER_ID] = df_2025.index.astype(str)

        if COL_OUTSTANDING_AMOUNT not in df_2025.columns:
            df_2025[COL_OUTSTANDING_AMOUNT] = 0.0

        if COL_APPROVED_AMOUNT not in df_2025.columns:
            df_2025[COL_APPROVED_AMOUNT] = df_2025[COL_OUTSTANDING_AMOUNT]

        # KPIs per segment
        summary = (
            df_2025.groupby(COL_CLIENT_SEGMENT)
            .agg(
                Clients=(COL_CUSTOMER_ID, "nunique"),
                Portfolio_Value=(COL_OUTSTANDING_AMOUNT, "sum"),
                Avg_Loan=(COL_APPROVED_AMOUNT, "mean"),
            )
            .reset_index()
        )

        # Join with delinquency if present
        if COL_DAYS_PAST_DUE in df_2025.columns:
            delinquent = df_2025[safe_numeric(df_2025[COL_DAYS_PAST_DUE]) > 30]
            delinquency_counts = delinquent.groupby(COL_CLIENT_SEGMENT).size()

            # Map back to summary
            total_clients = summary.set_index(COL_CLIENT_SEGMENT)["Clients"]
            delinquency_rate = (delinquency_counts / total_clients).fillna(0).round(
                3
            ) * 100
            summary["Delinquency_Rate"] = (
                summary[COL_CLIENT_SEGMENT].map(delinquency_rate).fillna(0)
            )

        # Main metric: Total Clients 2025
        total_active_clients = float(df_2025[COL_CUSTOMER_ID].nunique())

        return total_active_clients, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            segmentation_data=summary.to_dict(orient="records"),
            total_2025_clients=total_active_clients,
        )


def calculate_segmentation_summary(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Segmentation Summary calculation."""
    return SegmentationSummaryCalculator().calculate(df)
