import logging
from datetime import date, datetime
from functools import wraps
from typing import Callable, List, Optional

import numpy as np
import pandas as pd

from python.validation import find_column

logger = logging.getLogger(__name__)


def resolve_column(candidates: List[str], fallback: Optional[str] = None):
    """Decorator to resolve column name before method execution."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, df: pd.DataFrame, col_param: Optional[str] = None, **kwargs):
            resolved_col: Optional[str] = None
            if col_param and col_param in df.columns:
                resolved_col = col_param
            else:
                resolved_col = find_column(df, candidates)
                if not resolved_col and fallback and fallback in df.columns:
                    resolved_col = fallback
            if not resolved_col:
                logger.warning(
                    "Column not found for %s, tried: %s", func.__name__, candidates
                )
                return df
            return func(self, df, resolved_col, **kwargs)

        return wrapper

    return decorator


class Classification:
    """Classification rules and conditions."""

    @staticmethod
    def dpd_bucket_rules(val: float) -> str:
        """Map DPD value to bucket classification."""
        if val <= 0:
            return "Current"
        elif val <= 29:
            return "1-29"
        elif val <= 59:
            return "30-59"
        elif val <= 89:
            return "60-89"
        elif val <= 119:
            return "90-119"
        elif val <= 149:
            return "120-149"
        elif val <= 179:
            return "150-179"
        else:
            return "180+"

    @staticmethod
    def exposure_segment_rules(val: float) -> str:
        """Map exposure value to segment classification."""
        if val < 1000:
            return "Micro"
        elif val < 10000:
            return "Small"
        else:
            return "Medium/Large"

    @staticmethod
    def client_type_rules(loan_count: int, days_since_active: int) -> str:
        """Map loan metrics to client type classification."""
        if loan_count == 1:
            return "New"
        elif days_since_active <= 90:
            return "Recurring"
        else:
            return "Recovered"


class FinancialAnalyzer:
    """Financial analysis and enrichment engine."""

    def __init__(self):
        pass

    def validate_numeric_columns(self, df: pd.DataFrame, columns: list) -> list:
        """
        Batch numeric column validation. Returns list of errors.
        Raises ValueError if validation fails.
        """
        errors = []
        for col in columns:
            if col not in df.columns:
                errors.append(f"Missing column: {col}")
                df[col] = float("nan")
            elif not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} is not numeric")
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if errors:
            logger.error("Numeric column validation errors: %s", errors)
            raise ValueError(f"Numeric column validation errors: {errors}")
        return errors

    @resolve_column(["days_past_due", "dpd", "dias_mora", "days_late"])
    def classify_dpd_buckets(self, df: pd.DataFrame, dpd_col: str) -> pd.DataFrame:
        """Classify days past due into standard buckets."""
        result = df.copy()
        try:
            self.validate_numeric_columns(result, [dpd_col])
            result["dpd_bucket"] = result[dpd_col].apply(Classification.dpd_bucket_rules)
        except ValueError as e:
            logger.error("DPD classification failed: %s", e)
            result["dpd_bucket"] = "Unknown"
        return result

    @resolve_column(["outstanding_balance", "balance", "saldo", "amount"])
    def segment_clients_by_exposure(self, df: pd.DataFrame, exposure_col: str) -> pd.DataFrame:
        """Segment clients by exposure level."""
        result = df.copy()
        try:
            self.validate_numeric_columns(result, [exposure_col])
            result["exposure_segment"] = result[exposure_col].apply(
                Classification.exposure_segment_rules
            )
        except ValueError as e:
            logger.error("Exposure segmentation failed: %s", e)
            result["exposure_segment"] = "Unknown"
        return result

    def classify_client_type(
        self,
        df: pd.DataFrame,
        customer_id_col: str = "customer_id",
        loan_count_col: str = "loan_count",
        last_active_col: str = "last_active_date",
        reference_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Classify client type: New, Recurring, or Recovered."""
        result = df.copy()
        id_col = find_column(result, [customer_id_col, "client_id", "id_cliente"])

        if not id_col:
            logger.error("Customer ID column not found")
            return result

        count_col = find_column(result, [loan_count_col, "num_loans", "prestamos"])
        active_col = find_column(result, [last_active_col, "last_active", "ultima_actividad"])

        if count_col and active_col:
            try:
                self.validate_numeric_columns(result, [count_col])
                ref_date = pd.to_datetime(reference_date or datetime.now().date())
                result[active_col] = pd.to_datetime(result[active_col], errors="coerce")
                result["days_since_active"] = (ref_date - result[active_col]).dt.days
                result["client_type"] = result.apply(
                    lambda row: Classification.client_type_rules(
                        int(row[count_col]) if pd.notna(row[count_col]) else 0,
                        int(row["days_since_active"]) if pd.notna(row["days_since_active"]) else 0,
                    ),
                    axis=1,
                )
            except (ValueError, TypeError) as e:
                logger.error("Client type classification failed: %s", e)
                result["client_type"] = "Unknown"
        else:
            logger.warning("Missing columns for client type classification")
            result["client_type"] = "Unknown"

        return result

    def calculate_weighted_stats(
        self,
        loan_df: pd.DataFrame,
        weight_field: str = "outstanding_balance",
        metrics: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Calculate weighted statistics by weight field (e.g., OLB)."""
        default_metrics = ["apr", "eir", "term"]
        metrics = metrics or default_metrics

        weight_col = find_column(
            loan_df,
            [
                weight_field,
                "outstanding_balance",
                "olb",
                "current_balance",
                "saldo_actual",
                "balance",
            ],
        )
        if not weight_col:
            logger.error("Weight field not found, tried: %s", [weight_field])
            return pd.DataFrame()

        result = {}
        for stat in metrics:
            stat_col = find_column(loan_df, [stat])
            if stat_col:
                filtered_df = loan_df.dropna(subset=[stat_col, weight_col])
                if not filtered_df.empty and filtered_df[weight_col].sum() > 0:
                    weighted_avg = np.average(
                        filtered_df[stat_col], weights=filtered_df[weight_col]
                    )
                    result[f"weighted_{stat}"] = weighted_avg
                else:
                    logger.warning("No valid data for weighted %s", stat)

        return pd.DataFrame([result]) if result else pd.DataFrame()

    def calculate_line_utilization(
        self,
        loan_df: pd.DataFrame,
        credit_line_field: str = "line_amount",
        loan_amount_field: str = "outstanding_balance",
    ) -> pd.DataFrame:
        """Calculate credit line utilization rate."""
        result_df = loan_df.copy()

        credit_col = find_column(
            result_df, [credit_line_field, "credit_line", "line_limit", "limite_credito"]
        )
        loan_col = find_column(
            result_df,
            [loan_amount_field, "outstanding_balance", "olb", "current_balance", "loan_amount"],
        )

        if not credit_col or not loan_col:
            logger.warning("Line utilization columns not found")
            return result_df

        result_df["line_utilization"] = np.where(
            result_df[credit_col] > 0, result_df[loan_col] / result_df[credit_col], np.nan
        ).clip(0.0, 1.0)

        return result_df

    def calculate_hhi(
        self,
        loan_df: pd.DataFrame,
        customer_id_field: str = "customer_id",
        exposure_field: str = "outstanding_balance",
    ) -> float:
        """Calculate HHI (Herfindahl-Hirschman Index) for concentration."""
        exp_col = find_column(loan_df, [exposure_field, "balance", "saldo", "amount"])
        id_col = find_column(loan_df, [customer_id_field, "client_id", "id_cliente"])

        if not exp_col or not id_col:
            return 0.0

        customer_exposure = loan_df.groupby(id_col)[exp_col].sum()
        total_exposure = customer_exposure.sum()

        if total_exposure == 0:
            return 0.0

        market_shares = customer_exposure / total_exposure
        hhi = (market_shares**2).sum()
        return hhi * 10000

    def enrich_master_dataframe(
        self, df: pd.DataFrame, reference_date: Optional[date] = None
    ) -> pd.DataFrame:
        """Apply all feature engineering to master dataframe."""
        result = df.copy()

        result = self.classify_dpd_buckets(result)
        result = self.segment_clients_by_exposure(result)

        if all(col in result.columns for col in ["customer_id", "loan_count", "last_active_date"]):
            result = self.classify_client_type(result, reference_date=reference_date)

        result = self.calculate_line_utilization(result)

        key_metrics = ["apr", "term", "days_past_due", "outstanding_balance", "line_utilization"]
        for metric in key_metrics:
            if metric in result.columns and pd.api.types.is_numeric_dtype(result[metric]):
                std_dev = result[metric].std()
                if std_dev > 0:
                    result[f"{metric}_zscore"] = (result[metric] - result[metric].mean()) / std_dev

        return result
