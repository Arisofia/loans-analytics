import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from python.validation import (ANALYTICS_NUMERIC_COLUMNS,
                               REQUIRED_ANALYTICS_COLUMNS,
                               assert_dataframe_schema, find_column)

logger = logging.getLogger(__name__)


class DataTransformation:
    REQUIRED_INPUT_COLUMNS = [
        "total_receivable_usd",
        "total_eligible_usd",
        "discounted_balance_usd",
        "dpd_0_7_usd",
        "dpd_7_30_usd",
        "dpd_30_60_usd",
        "dpd_60_90_usd",
        "dpd_90_plus_usd",
    ]

    REQUIRED_ANALYTICS_COLUMNS = REQUIRED_ANALYTICS_COLUMNS

    COLUMN_MAPPINGS = {
        "loan_amount": ["receivable_amount"],
        "principal_balance": ["discounted_amount"],
        "interest_rate": ["avg_apr_pct"],
    }

    def __init__(self):
        self.run_id = f"tx_{uuid.uuid4().hex[:16]}"
        self.transformations_count = 0
        self.timestamp: Optional[str] = None
        self.lineage: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        for key, value in context.items():
            if value is not None:
                self.context[key] = value

    def _log_transformation(self, step: str, message: str, **details: Any) -> None:
        detail_parts = [f"{key}={value!r}" for key, value in details.items() if value is not None]
        context_parts = [
            f"{key}={value!r}" for key, value in self.context.items() if value is not None
        ]
        segments = [f"[transformation:{step}]", message]
        if detail_parts:
            segments.append(", ".join(detail_parts))
        if context_parts:
            segments.append(f"context({', '.join(context_parts)})")
        logger.info(" | ".join(segments))

    def _record_lineage(
        self,
        step: str,
        input_columns: List[str],
        output_columns: List[str],
        details: Dict[str, Any],
    ) -> None:
        entry: Dict[str, Any] = {
            "step": step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "input_columns": input_columns,
            "output_columns": output_columns,
            "details": details,
            "context": self.context.copy(),
        }
        self.lineage.append(entry)

    def get_lineage(self) -> List[Dict[str, Any]]:
        return list(self.lineage)

    def get_processing_summary(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "processed_at": self.timestamp,
            "transformations_count": self.transformations_count,
            "context": self.context.copy(),
        }

    def calculate_receivables_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        self._log_transformation(
            "calculate_receivables_metrics", "Calculating receivables metrics", rows=len(df)
        )
        metrics = {
            "total_receivable": df["total_receivable_usd"].sum(),
            "total_eligible": df["total_eligible_usd"].sum(),
            "discounted_balance": df["discounted_balance_usd"].sum(),
        }
        self._record_lineage(
            "calculate_receivables_metrics",
            list(df.columns),
            [],
            {"metrics": metrics, "rows": len(df)},
        )
        return metrics

    def calculate_dpd_ratios(self, df: pd.DataFrame) -> Dict[str, float]:
        self._log_transformation("calculate_dpd_ratios", "Calculating DPD ratios", rows=len(df))
        total = df["total_receivable_usd"].sum()
        if total == 0:
            self._record_lineage(
                "calculate_dpd_ratios",
                list(df.columns),
                [],
                {"ratios": {}, "rows": len(df)},
            )
            return {}
        ratios: Dict[str, float] = {}
        for col in [
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]:
            if col in df.columns:
                ratios[col] = (df[col].sum() / total) * 100.0
        self._record_lineage(
            "calculate_dpd_ratios",
            list(df.columns),
            [],
            {"ratios": ratios, "rows": len(df)},
        )
        return ratios

    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw loan data into a KPI-ready dataset with ratios, analytics columns, and metadata."""
        self._log_transformation(
            "transform_to_kpi_dataset", "Starting KPI dataset transformation", rows=len(df)
        )
        missing = [c for c in self.REQUIRED_INPUT_COLUMNS if c not in df.columns]
        if missing:
            self._log_transformation(
                "transform_to_kpi_dataset", "Missing required columns", missing_columns=missing
            )
            raise ValueError(f"Transformation failed: missing required columns: {missing}")

        # Check for non-numeric required columns and raise ValueError
        for col in self.REQUIRED_INPUT_COLUMNS:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Transformation failed: must be numeric: {col}")

        try:
            assert_dataframe_schema(
                df,
                required_columns=self.REQUIRED_INPUT_COLUMNS,
                numeric_columns=self.REQUIRED_INPUT_COLUMNS,
                stage="transformation_input",
            )
        except AssertionError as error:
            message = str(error)
            self._log_transformation(
                "transform_to_kpi_dataset", "Input schema assertion failed", error=message
            )
            raise ValueError(f"Transformation failed: {message}") from error

        kpi_df = df.copy()
        # Create aliases for clarity but keep original names for compatibility with KPI engine
        kpi_df["receivable_amount"] = kpi_df["total_receivable_usd"]
        kpi_df["eligible_amount"] = kpi_df["total_eligible_usd"]
        kpi_df["discounted_amount"] = kpi_df["discounted_balance_usd"]

        receivable = kpi_df["receivable_amount"].replace(0, np.nan)
        for col in [
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]:
            if col in df.columns:
                kpi_df[f"{col}_pct"] = (df[col] / receivable).fillna(0.0) * 100

        for col in self.REQUIRED_ANALYTICS_COLUMNS:
            if col not in kpi_df.columns:
                candidates = self.COLUMN_MAPPINGS.get(col, [])
                source_col = find_column(kpi_df, candidates)
                if source_col:
                    kpi_df[col] = kpi_df[source_col]
                elif col == "loan_status":
                    kpi_df[col] = "unknown"
                else:
                    kpi_df[col] = float("nan")

        transform_ts = datetime.now(timezone.utc).isoformat()
        self.timestamp = transform_ts
        kpi_df["_transform_run_id"] = self.run_id
        kpi_df["_transform_timestamp"] = transform_ts

        self._log_transformation("transform_to_kpi_dataset", "KPI dataset ready", rows=len(kpi_df))
        try:
            assert_dataframe_schema(
                kpi_df,
                required_columns=self.REQUIRED_ANALYTICS_COLUMNS,
                numeric_columns=ANALYTICS_NUMERIC_COLUMNS,
                stage="transformation_output",
            )
        except AssertionError as error:
            message = str(error)
            self._log_transformation(
                "transform_to_kpi_dataset", "Output schema assertion failed", error=message
            )
            raise ValueError(f"Transformation output invalid: {message}") from error
        self._record_lineage(
            "transform_to_kpi_dataset",
            list(df.columns),
            list(kpi_df.columns),
            {
                "rows": len(kpi_df),
                "required_columns": self.REQUIRED_INPUT_COLUMNS,
                "analytics_columns": [
                    col for col in self.REQUIRED_ANALYTICS_COLUMNS if col in kpi_df.columns
                ],
            },
        )
        self.transformations_count += 1
        return kpi_df

    def validate_transformations(self, original: pd.DataFrame, transformed: pd.DataFrame) -> bool:
        self._log_transformation(
            "validate_transformations",
            "Validating transformation integrity",
            original_rows=len(original),
            transformed_rows=len(transformed),
        )
        if len(original) != len(transformed):
            return False
        if (
            "total_receivable_usd" in original.columns
            and "receivable_amount" in transformed.columns
        ):
            orig_sum = original["total_receivable_usd"].sum()
            trans_sum = transformed["receivable_amount"].sum()
            if not np.isclose(orig_sum, trans_sum):
                return False
        return True
