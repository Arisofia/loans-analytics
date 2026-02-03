"""
KPIEngineV2: Standardized KPI calculation engine with built-in audit trails.

This module provides a unified interface for KPI calculations across the Abaco
loans analytics platform, replacing the v1 approach of individual function calls.

Features:
- Standardized (value, context) tuple return format
- Built-in audit trail with timestamps and actor tracking
- Individual KPI failure isolation (doesn't crash entire pipeline)
- Traceability for compliance and debugging

Usage:
    from python.kpis.engine import KPIEngineV2

    engine = KPIEngineV2(df, actor="reporting_service", run_id="2026-01-29-001")
    metrics = engine.calculate_all()
    par30_val = metrics["PAR30"]["value"]

    # Export audit trail for compliance
    audit_df = engine.get_audit_trail()
    audit_df.to_csv("exports/kpi_audit_trail.csv", index=False)
"""

from __future__ import annotations

import json
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.par_30 import calculate_par_30
from python.logging_config import get_logger

logger = get_logger(__name__)

# Log message format constants
_LOG_KPI_CALCULATED = "Calculated %s: %s"


def _handle_kpi_calculation_error(kpi_name: str) -> Callable:
    """
    Decorator to handle errors in KPI calculations consistently.

    Returns 0.0 as fallback value on error and records the error in audit trail.
    Note: 0.0 is used as a neutral fallback to prevent pipeline crashes while
    maintaining audit trail visibility of failures. Consumers should check the
    context for "error" key before using the value.

    Args:
        kpi_name: Name of the KPI being calculated

    Returns:
        Decorated function with error handling
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Tuple[float, Dict[str, Any]]:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                logger.error("Failed to calculate %s: %s", kpi_name, error_msg)
                fallback_value = 0.0
                error_context = {"error": error_msg}
                self._record_calculation(  # pylint: disable=protected-access
                    kpi_name, fallback_value, error_context, error_msg
                )
                return fallback_value, error_context

        return wrapper

    return decorator


class KPIEngineV2:
    """
    Unified KPI calculation engine with audit trail support.

    All KPI calculators return a consistent (value, context) tuple format,
    and every calculation is logged in an audit trail with timestamps,
    actor information, and run IDs for full traceability.
    """

    def __init__(self, df: pd.DataFrame, actor: str = "system", run_id: Optional[str] = None):
        """
        Initialize KPI engine.

        Args:
            df: Input DataFrame with loan/payment data
            actor: Identity of the entity requesting calculations. Examples:
                "reporting_service", "api", "user:john@example.com"
            run_id: Optional unique identifier for this calculation run
        """
        self.df = df
        self.actor = actor
        self.run_id = run_id or self._generate_run_id()
        self._audit_records: List[Dict[str, Any]] = []

        logger.info("Initialized KPIEngineV2 with actor=%s, run_id=%s", actor, self.run_id)

    def _generate_run_id(self) -> str:
        """Generate a unique run ID based on timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _record_calculation(
        self,
        kpi_name: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record a KPI calculation in the audit trail.

        Args:
            kpi_name: Name of the KPI (e.g., "PAR30", "LTV")
            value: Calculated value (can be None if error occurred)
            context: Additional context about the calculation
            error: Error message if calculation failed
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "actor": self.actor,
            "kpi_name": kpi_name,
            "value": value,
            "context": context or {},
            "error": error,
            "status": "success" if error is None else "failed",
        }
        self._audit_records.append(record)

    @_handle_kpi_calculation_error("PAR30")
    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Portfolio at Risk (30+ days).

        Returns:
            Tuple of (value, context) where:
            - value: PAR30 percentage (0.0 if calculation fails)
            - context: Dict with calculation details or error message
        """
        kpi_name = "PAR30"
        value = calculate_par_30(self.df)
        context = {
            "formula": "SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable) * 100",
            "rows_processed": len(self.df),
            "calculation_method": "v1_legacy",
        }
        self._record_calculation(kpi_name, value, context)
        logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)
        return value, context

    @_handle_kpi_calculation_error("COLLECTION_RATE")
    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate collection rate.

        Returns:
            Tuple of (value, context) where:
            - value: Collection rate percentage (0.0 if calculation fails)
            - context: Dict with calculation details or error message
        """
        kpi_name = "COLLECTION_RATE"
        value, _ = calculate_collection_rate(self.df)
        context = {
            "formula": "payments_collected / payments_due * 100",
            "rows_processed": len(self.df),
            "calculation_method": "v1_legacy",
        }
        self._record_calculation(kpi_name, value, context)
        logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)
        return value, context

    @_handle_kpi_calculation_error("LTV")
    def calculate_ltv(self) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Loan-to-Value ratio (on-demand KPI).

        Returns:
            Tuple of (value, context) where:
            - value: LTV percentage (0.0 if calculation fails or columns missing)
            - context: Dict with calculation details, error message, or missing columns info
        """
        kpi_name = "LTV"

        # Check for required columns
        required_columns = ["loan_amount", "collateral_value"]
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            # Record as successful but with missing data context
            value = 0.0
            context = {
                "formula": "total_loan_amount / total_collateral_value * 100",
                "rows_processed": len(self.df),
                "calculation_method": "v2_engine",
                "missing_columns": missing_columns,
                "calculation_status": "missing_required_columns",
            }
            error_msg = f"Missing required columns for {kpi_name}: {', '.join(missing_columns)}"
            logger.warning(error_msg)
            self._record_calculation(kpi_name, value, context, error_msg)
            return value, context

        # Calculate LTV with available data
        total_loans = self.df["loan_amount"].sum()
        total_collateral = self.df["collateral_value"].sum()
        value = (total_loans / total_collateral * 100) if total_collateral > 0 else 0.0

        context = {
            "formula": "total_loan_amount / total_collateral_value * 100",
            "rows_processed": len(self.df),
            "calculation_method": "v2_engine",
        }
        self._record_calculation(kpi_name, value, context)
        logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)
        return value, context

    def calculate_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate all standard KPIs.

        Returns:
            Dict mapping KPI names to dicts with "value" and "context" keys.
            Individual KPI failures are captured in the result dict and don't
            crash the entire pipeline.

        Example:
            {
                "PAR30": {"value": 5.2, "context": {...}},
                "COLLECTION_RATE": {"value": 97.5, "context": {...}}
            }
        """
        logger.info("Calculating all standard KPIs")

        results = {}

        # Calculate each KPI and capture failures
        par30_val, par30_ctx = self.calculate_par_30()
        results["PAR30"] = {"value": par30_val, "context": par30_ctx}

        coll_rate_val, coll_rate_ctx = self.calculate_collection_rate()
        results["COLLECTION_RATE"] = {"value": coll_rate_val, "context": coll_rate_ctx}

        logger.info("Calculated %d KPIs", len(results))
        return results

    def get_audit_trail(self) -> pd.DataFrame:
        """
        Export the calculation audit trail as a DataFrame.

        Returns:
            DataFrame with columns: timestamp, run_id, actor, kpi_name, value,
            context, error, status

        Example:
            audit_df = engine.get_audit_trail()
            audit_df.to_csv("kpi_audit_log.csv", index=False)
        """
        if not self._audit_records:
            logger.warning("No audit records available")
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "run_id",
                    "actor",
                    "kpi_name",
                    "value",
                    "context",
                    "error",
                    "status",
                ]
            )

        # Convert context dicts to JSON strings for CSV export
        records_for_df = []
        for record in self._audit_records:
            record_copy = record.copy()
            # Use json.dumps for proper JSON serialization instead of str()
            context_value = record_copy.get("context", {})
            if context_value is not None:
                record_copy["context"] = json.dumps(context_value)
            else:
                record_copy["context"] = json.dumps({})
            records_for_df.append(record_copy)

        df = pd.DataFrame(records_for_df)
        logger.info("Generated audit trail with %d records", len(df))
        return df
