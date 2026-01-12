"""
Complete KPI calculator for ABACO portfolio analytics.
This module provides a high-level API for computing a comprehensive set of KPIs.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from src.analytics.kpi_catalog_processor import KPICatalogProcessor


class ABACOKPICalculator:
    """
    Main entry point for computing all portfolio KPIs.
    Delegates to KPICatalogProcessor for detailed metric generation.
    """

    def __init__(
        self,
        loans_df: pd.DataFrame,
        payments_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        schedule_df: pd.DataFrame | None = None,
    ):
        self.processor = KPICatalogProcessor(
            loans_df=loans_df,
            payments_df=payments_df,
            customers_df=customers_df,
            schedule_df=schedule_df,
        )

    def get_complete_kpi_dashboard(self, cac_usd: float = 350.0) -> Dict[str, Any]:
        """
        Returns a consolidated dashboard of all KPIs.
        """
        kpis = self.processor.get_all_kpis()
        
        # Add some top-level summary metrics if available in executive strip
        exec_strip = kpis.get("executive_strip", {})
        summary = {
            "total_aum_usd": exec_strip.get("total_aum", 0.0),
            "active_customers": exec_strip.get("active_customers", 0),
            "par_90_ratio_pct": exec_strip.get("par_90", 0.0),
            "weighted_avg_apr": exec_strip.get("avg_apr", 0.0),
        }
        
        return {**summary, "extended_kpis": kpis}

    def get_active_clients(self) -> int:
        """Returns the number of active unique customers."""
        exec_strip = self.processor.get_executive_strip()
        return int(exec_strip.get("active_customers", 0))

    def get_total_aum(self) -> float:
        """Returns total Assets Under Management."""
        exec_strip = self.processor.get_executive_strip()
        return float(exec_strip.get("total_aum", 0.0))

    def get_aum_by_customer_type(self) -> pd.DataFrame:
        """Returns a breakdown of AUM by customer type."""
        return self.processor.get_customer_types()


def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Backward compatibility with simple pipeline runs."""
    from src.analytics.run_pipeline import calculate_kpis as run_calc
    return run_calc(df)


def create_metrics_csv(df: pd.DataFrame, output_path: Any) -> None:
    """Backward compatibility with simple pipeline runs."""
    from src.analytics.run_pipeline import create_metrics_csv as run_csv
    run_csv(df, output_path)
