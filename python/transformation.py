import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from python.validation import (
    ANALYTICS_NUMERIC_COLUMNS,
    REQUIRED_ANALYTICS_COLUMNS,
    assert_dataframe_schema,
    find_column,
)

logger = logging.getLogger(__name__)


class ColumnDefinition:
    """Define source and target columns for transformation."""
    
    DPD_COLUMNS = ["dpd_0_7_usd", "dpd_7_30_usd", "dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd"]
    ALIAS_MAPPINGS = {
        "loan_amount": ["receivable_amount"],
        "principal_balance": ["discounted_amount"],
        "interest_rate": ["avg_apr_pct"],
    }


class DataTransformation:
    """Transform raw data into KPI-ready dataset with lineage tracking."""

    REQUIRED_INPUT_COLUMNS = [
        "total_receivable_usd",
        "total_eligible_usd",
        "discounted_balance_usd",
    ] + ColumnDefinition.DPD_COLUMNS

    REQUIRED_ANALYTICS_COLUMNS = REQUIRED_ANALYTICS_COLUMNS

    def __init__(self):
        self.run_id = f"tx_{uuid.uuid4().hex[:16]}"
        self.transformations_count = 0
        self.timestamp: Optional[str] = None
        self.lineage: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        """Set contextual metadata for logging."""
        for key, value in context.items():
            if value is not None:
                self.context[key] = value

    def _format_log_details(self, **details: Any) -> str:
        """Format details and context for logging."""
        detail_parts = [f"{k}={v!r}" for k, v in details.items() if v is not None]
        context_parts = [f"{k}={v!r}" for k, v in self.context.items() if v is not None]
        all_parts = detail_parts + context_parts
        return ", ".join(all_parts) if all_parts else ""

    def _log_and_record(
        self,
        step: str,
        message: str,
        input_cols: List[str],
        output_cols: List[str],
        details: Dict[str, Any],
        **log_details
    ) -> None:
        """Log step and record lineage in one call."""
        log_msg = f"[transformation:{step}] {message}"
        if log_details:
            log_msg += f" | {self._format_log_details(**log_details)}"
        logger.info(log_msg)

        entry: Dict[str, Any] = {
            "step": step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "input_columns": input_cols,
            "output_columns": output_cols,
            "details": details,
            "context": self.context.copy(),
        }
        self.lineage.append(entry)

    def get_lineage(self) -> List[Dict[str, Any]]:
        """Return lineage records."""
        return list(self.lineage)

    def get_processing_summary(self) -> Dict[str, Any]:
        """Return processing summary."""
        return {
            "run_id": self.run_id,
            "processed_at": self.timestamp,
            "transformations_count": self.transformations_count,
            "context": self.context.copy(),
        }

    def _calculate_ratio(self, df: pd.DataFrame, numerator_col: str, denominator_col: str) -> float:
        """Calculate percentage ratio safely."""
        numerator = df[numerator_col].sum()
        denominator = df[denominator_col].sum()
        if denominator == 0:
            return 0.0
        return (numerator / denominator) * 100.0

    def calculate_receivables_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate receivables metrics summary."""
        metrics = {
            "total_receivable": df["total_receivable_usd"].sum(),
            "total_eligible": df["total_eligible_usd"].sum(),
            "discounted_balance": df["discounted_balance_usd"].sum(),
        }
        self._log_and_record(
            "calculate_receivables_metrics",
            "Calculating receivables metrics",
            list(df.columns),
            [],
            {"metrics": metrics, "rows": len(df)},
            rows=len(df)
        )
        return metrics

    def calculate_dpd_ratios(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate DPD buckets as percentage of total receivable."""
        total = df["total_receivable_usd"].sum()
        ratios = {}
        
        if total > 0:
            for col in ColumnDefinition.DPD_COLUMNS:
                if col in df.columns:
                    ratios[col] = (df[col].sum() / total) * 100.0
        
        self._log_and_record(
            "calculate_dpd_ratios",
            "Calculating DPD ratios",
            list(df.columns),
            [],
            {"ratios": ratios, "rows": len(df)},
            rows=len(df)
        )
        return ratios

    def _create_column_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create convenience column aliases."""
        result = df.copy()
        result["receivable_amount"] = result["total_receivable_usd"]
        result["eligible_amount"] = result["total_eligible_usd"]
        result["discounted_amount"] = result["discounted_balance_usd"]
        return result

    def _add_dpd_percentages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add DPD columns as percentages of total receivable."""
        result = df.copy()
        receivable = result["receivable_amount"].replace(0, np.nan)
        
        for col in ColumnDefinition.DPD_COLUMNS:
            if col in result.columns:
                result[f"{col}_pct"] = (result[col] / receivable).fillna(0.0) * 100
        
        return result

    def _add_analytics_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing analytics columns from mappings or defaults."""
        result = df.copy()
        
        for col in self.REQUIRED_ANALYTICS_COLUMNS:
            if col not in result.columns:
                candidates = ColumnDefinition.ALIAS_MAPPINGS.get(col, [])
                source_col = find_column(result, candidates)
                
                if source_col:
                    result[col] = result[source_col]
                elif col == "loan_status":
                    result[col] = "unknown"
                else:
                    result[col] = float("nan")
        
        return result

    def _validate_schema(self, df: pd.DataFrame, schema_type: str, stage: str) -> None:
        """Validate DataFrame schema."""
        try:
            if schema_type == "input":
                assert_dataframe_schema(
                    df,
                    required_columns=self.REQUIRED_INPUT_COLUMNS,
                    numeric_columns=self.REQUIRED_INPUT_COLUMNS,
                    stage=stage,
                )
            elif schema_type == "output":
                assert_dataframe_schema(
                    df,
                    required_columns=self.REQUIRED_ANALYTICS_COLUMNS,
                    numeric_columns=ANALYTICS_NUMERIC_COLUMNS,
                    stage=stage,
                )
        except AssertionError as e:
            raise ValueError(f"{stage} schema validation failed: {e}") from e

    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw loan data into KPI-ready dataset."""
        self._log_and_record(
            "transform_to_kpi_dataset",
            "Starting transformation",
            list(df.columns),
            [],
            {"rows": len(df)},
            rows=len(df)
        )

        missing = [c for c in self.REQUIRED_INPUT_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        self._validate_schema(df, "input", "transformation_input")

        kpi_df = self._create_column_aliases(df)
        kpi_df = self._add_dpd_percentages(kpi_df)
        kpi_df = self._add_analytics_columns(kpi_df)

        transform_ts = datetime.now(timezone.utc).isoformat()
        self.timestamp = transform_ts
        kpi_df["_transform_run_id"] = self.run_id
        kpi_df["_transform_timestamp"] = transform_ts

        self._validate_schema(kpi_df, "output", "transformation_output")

        self._log_and_record(
            "transform_to_kpi_dataset",
            "Transformation complete",
            list(df.columns),
            list(kpi_df.columns),
            {
                "rows": len(kpi_df),
                "output_columns": len(kpi_df.columns),
            },
            rows=len(kpi_df)
        )
        
        self.transformations_count += 1
        return kpi_df

    def validate_transformations(self, original: pd.DataFrame, transformed: pd.DataFrame) -> bool:
        """Validate transformation preserves data integrity."""
        if len(original) != len(transformed):
            return False
        
        if "total_receivable_usd" in original.columns and "receivable_amount" in transformed.columns:
            orig_sum = original["total_receivable_usd"].sum()
            trans_sum = transformed["receivable_amount"].sum()
            if not np.isclose(orig_sum, trans_sum):
                return False
        
        self._log_and_record(
            "validate_transformations",
            "Transformation validation passed",
            [],
            [],
            {"original_rows": len(original), "transformed_rows": len(transformed)}
        )
        
        return True
