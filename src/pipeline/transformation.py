"""
PHASE 2: DATA TRANSFORMATION

Responsibilities:
- Data cleaning and normalization
- Null/outlier handling
- Type conversion
- Business rules application
- Referential integrity checks
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from python.logging_config import get_logger

logger = get_logger(__name__)


class TransformationPhase:
    """Phase 2: Data Transformation"""

    # Default numeric columns for financial data
    NUMERIC_COLUMNS: Set[str] = {
        "amount",
        "current_balance",
        "original_amount",
        "interest_rate",
        "dpd",
        "payment_amount",
    }

    # Default date columns
    DATE_COLUMNS: Set[str] = {
        "disbursement_date",
        "origination_date",
        "due_date",
        "payment_date",
        "measurement_date",
    }

    # Status mappings for normalization
    STATUS_MAPPINGS: Dict[str, str] = {
        "Active": "active",
        "ACTIVE": "active",
        "Delinquent": "delinquent",
        "DELINQUENT": "delinquent",
        "Closed": "closed",
        "CLOSED": "closed",
        "Defaulted": "defaulted",
        "DEFAULTED": "defaulted",
        "default": "defaulted",
    }

    # Null handling thresholds and constants
    LOW_NULL_THRESHOLD_PCT: float = 5.0  # Below this: fill with median/mode
    HIGH_NULL_THRESHOLD_PCT: float = 30.0  # Above this: use default fill
    MISSING_NUMERIC_INDICATOR: int = -999  # Indicator for missing numeric values

    def __init__(self, config: Dict[str, Any], business_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize transformation phase.

        Args:
            config: Transformation configuration from pipeline.yml
            business_rules: Business rules from business_rules.yaml
        """
        self.config = config
        self.business_rules = business_rules or {}

        # Extract configuration settings with defaults
        null_config = config.get("null_handling", {})
        self.null_strategy = null_config.get("strategy", "smart")
        self.fill_values = null_config.get(
            "fill_values", {"numeric": 0, "categorical": "unknown"}
        )

        outlier_config = config.get("outlier_detection", {})
        self.outlier_enabled = outlier_config.get("enabled", True)
        self.outlier_method = outlier_config.get("method", "iqr")
        self.outlier_threshold = outlier_config.get("threshold", 3.0)

        type_config = config.get("type_normalization", {})
        self.type_normalization_enabled = type_config.get("enabled", True)
        self.date_format = type_config.get("date_format", "%Y-%m-%d")

        logger.info("Initialized transformation phase")

    def execute(
        self,
        raw_data_path: Optional[Path] = None,
        df: Optional[pd.DataFrame] = None,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute transformation phase.

        Args:
            raw_data_path: Path to raw data from Phase 1
            df: DataFrame (if already loaded)
            run_dir: Directory for this pipeline run

        Returns:
            Transformation results including cleaned data path
        """
        logger.info("Starting Phase 2: Transformation")

        try:
            # Load data
            if df is None:
                if raw_data_path and raw_data_path.exists():
                    df = pd.read_parquet(raw_data_path)
                else:
                    raise ValueError("No data provided for transformation")

            initial_rows = len(df)
            transformation_metrics: Dict[str, Any] = {}

            # Apply transformations with metrics tracking
            df, null_metrics = self._handle_nulls(df)
            transformation_metrics["null_handling"] = null_metrics

            df, type_metrics = self._normalize_types(df)
            transformation_metrics["type_normalization"] = type_metrics

            df, rule_metrics = self._apply_business_rules(df)
            transformation_metrics["business_rules"] = rule_metrics

            df, outlier_metrics = self._detect_outliers(df)
            transformation_metrics["outlier_detection"] = outlier_metrics

            df, integrity_metrics = self._check_referential_integrity(df)
            transformation_metrics["referential_integrity"] = integrity_metrics

            # Store clean data
            if run_dir:
                output_path = run_dir / "clean_data.parquet"
                df.to_parquet(output_path, index=False)
                logger.info(f"Saved clean data to {output_path}")
            else:
                output_path = None

            results = {
                "status": "success",
                "initial_rows": initial_rows,
                "final_rows": len(df),
                "rows_removed": initial_rows - len(df),
                "columns": len(df.columns),
                "output_path": str(output_path) if output_path else None,
                "transformation_metrics": transformation_metrics,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Transformation completed: {initial_rows} → {len(df)} rows")
            return results

        except Exception as e:
            logger.error(f"Transformation failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _handle_nulls(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing values based on configured strategy.

        Strategies:
        - 'drop': Remove rows with any null values
        - 'fill': Fill nulls with configured default values
        - 'smart': Intelligent handling based on column type and null percentage

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metrics dict)
        """
        logger.info(f"Handling null values (strategy: {self.null_strategy})")

        initial_nulls = df.isnull().sum()
        total_nulls = initial_nulls.sum()
        null_columns = initial_nulls[initial_nulls > 0].to_dict()

        if total_nulls == 0:
            logger.info("No null values found")
            return df, {"total_nulls": 0, "strategy_applied": "none", "columns_affected": []}

        metrics = {
            "initial_total_nulls": int(total_nulls),
            "null_columns": null_columns,
            "strategy_applied": self.null_strategy,
            "columns_affected": list(null_columns.keys()),
        }

        if self.null_strategy == "drop":
            rows_before = len(df)
            df = df.dropna()
            rows_dropped = rows_before - len(df)
            metrics["rows_dropped"] = rows_dropped
            logger.info(f"Dropped {rows_dropped} rows with null values")

        elif self.null_strategy == "fill":
            df = self._fill_nulls_by_type(df)
            metrics["fill_values_used"] = self.fill_values
            logger.info("Filled null values with configured defaults")

        elif self.null_strategy == "smart":
            df, smart_metrics = self._smart_null_handling(df, null_columns)
            metrics.update(smart_metrics)
            logger.info("Applied smart null handling")

        final_nulls = df.isnull().sum().sum()
        metrics["final_total_nulls"] = int(final_nulls)

        return df, metrics

    def _fill_nulls_by_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill nulls based on column data type."""
        for col in df.columns:
            if df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(self.fill_values.get("numeric", 0))
                else:
                    df[col] = df[col].fillna(self.fill_values.get("categorical", "unknown"))
        return df

    def _smart_null_handling(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intelligent null handling based on null percentage and column importance.

        Uses configurable thresholds:
        - < LOW_NULL_THRESHOLD_PCT: Fill with median (numeric) or mode (categorical)
        - LOW to HIGH_NULL_THRESHOLD_PCT: Fill with missing indicator
        - > HIGH_NULL_THRESHOLD_PCT: Log warning, fill with default
        """
        actions: Dict[str, str] = {}
        total_rows = len(df)

        for col, null_count in null_columns.items():
            null_pct = null_count / total_rows * 100

            if pd.api.types.is_numeric_dtype(df[col]):
                if null_pct < self.LOW_NULL_THRESHOLD_PCT:
                    median_val = df[col].median()
                    if pd.isna(median_val):
                        median_val = 0
                    df[col] = df[col].fillna(median_val)
                    actions[col] = f"filled_median ({median_val:.2f})"
                elif null_pct < self.HIGH_NULL_THRESHOLD_PCT:
                    df[col] = df[col].fillna(self.MISSING_NUMERIC_INDICATOR)
                    actions[col] = f"filled_missing_indicator ({self.MISSING_NUMERIC_INDICATOR})"
                else:
                    df[col] = df[col].fillna(0)
                    actions[col] = f"filled_zero (high_null: {null_pct:.1f}%)"
                    logger.warning(f"Column '{col}' has {null_pct:.1f}% nulls")
            else:
                if null_pct < self.LOW_NULL_THRESHOLD_PCT:
                    mode_val = df[col].mode()
                    fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
                    df[col] = df[col].fillna(fill_val)
                    actions[col] = f"filled_mode ({fill_val})"
                else:
                    df[col] = df[col].fillna("missing")
                    actions[col] = "filled_missing_label"

        return df, {"smart_actions": actions}

    def _normalize_types(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize data types for consistency.

        - Convert date strings to datetime
        - Ensure numeric columns are proper numeric types
        - Standardize string formats (lowercase status, etc.)

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metrics dict)
        """
        logger.info("Normalizing data types")

        if not self.type_normalization_enabled:
            return df, {"enabled": False}

        conversions: Dict[str, Dict[str, str]] = {}

        # Normalize date columns
        for col in df.columns:
            if col in self.DATE_COLUMNS or col.endswith("_date"):
                if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
                    try:
                        df[col] = pd.to_datetime(df[col], format=self.date_format, errors="coerce")
                        conversions[col] = {"from": "string", "to": "datetime64"}
                    except Exception as e:
                        logger.warning(f"Could not convert {col} to datetime: {e}")

        # Normalize numeric columns
        for col in df.columns:
            if col in self.NUMERIC_COLUMNS or any(
                kw in col.lower() for kw in ["amount", "balance", "rate", "count", "dpd"]
            ):
                if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
                    try:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                        conversions[col] = {"from": "string", "to": "numeric"}
                    except Exception as e:
                        logger.warning(f"Could not convert {col} to numeric: {e}")

        # Normalize status column if present
        if "status" in df.columns:
            original_values = df["status"].unique().tolist()
            df["status"] = df["status"].apply(
                lambda x: self.STATUS_MAPPINGS.get(x, str(x).lower() if pd.notna(x) else x)
            )
            conversions["status"] = {"normalized_values": original_values}

        metrics = {
            "enabled": True,
            "conversions_applied": len(conversions),
            "conversion_details": conversions,
        }

        logger.info(f"Applied {len(conversions)} type conversions")
        return df, metrics

    def _apply_business_rules(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply business rules from configuration.

        Applies:
        - Status mappings and validations
        - DPD bucket assignments
        - Risk categorization
        - Custom field derivations

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metrics dict)
        """
        logger.info("Applying business rules")

        rules_applied: List[str] = []
        fields_created: List[str] = []

        # Apply DPD bucket assignment if dpd column exists
        if "dpd" in df.columns:
            df["dpd_bucket"] = df["dpd"].apply(self._assign_dpd_bucket)
            fields_created.append("dpd_bucket")
            rules_applied.append("dpd_bucket_assignment")

        # Apply risk categorization based on multiple factors
        if "status" in df.columns and "dpd" in df.columns:
            df["risk_category"] = df.apply(self._calculate_risk_category, axis=1)
            fields_created.append("risk_category")
            rules_applied.append("risk_categorization")

        # Apply amount tier classification if amount column exists
        if "amount" in df.columns:
            df["amount_tier"] = df["amount"].apply(self._assign_amount_tier)
            fields_created.append("amount_tier")
            rules_applied.append("amount_tier_classification")

        # Apply custom business rules from configuration
        custom_rules = self.business_rules.get("transformations", [])
        for rule in custom_rules:
            try:
                df = self._apply_custom_rule(df, rule)
                rules_applied.append(rule.get("name", "unnamed_rule"))
            except Exception as e:
                logger.warning(f"Failed to apply custom rule: {e}")

        metrics = {
            "rules_applied": len(rules_applied),
            "rule_names": rules_applied,
            "fields_created": fields_created,
        }

        logger.info(f"Applied {len(rules_applied)} business rules")
        return df, metrics

    def _assign_dpd_bucket(self, dpd: float) -> str:
        """Assign DPD (Days Past Due) bucket."""
        if pd.isna(dpd) or dpd < 0:
            return "unknown"
        elif dpd == 0:
            return "current"
        elif dpd < 30:
            return "1-29"
        elif dpd < 60:
            return "30-59"
        elif dpd < 90:
            return "60-89"
        elif dpd < 180:
            return "90-179"
        else:
            return "180+"

    def _calculate_risk_category(self, row: pd.Series) -> str:
        """Calculate risk category based on status and DPD."""
        status = row.get("status", "")
        dpd = row.get("dpd", 0)

        if status == "defaulted":
            return "critical"
        elif status == "delinquent" or (pd.notna(dpd) and dpd >= 90):
            return "high"
        elif pd.notna(dpd) and dpd >= 30:
            return "medium"
        elif status == "active" and (pd.isna(dpd) or dpd < 30):
            return "low"
        else:
            return "unknown"

    def _assign_amount_tier(self, amount: float) -> str:
        """Assign loan amount tier."""
        if pd.isna(amount) or amount <= 0:
            return "invalid"
        elif amount < 5000:
            return "micro"
        elif amount < 25000:
            return "small"
        elif amount < 100000:
            return "medium"
        elif amount < 500000:
            return "large"
        else:
            return "jumbo"

    def _apply_custom_rule(self, df: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply a custom business rule from configuration.

        Note: Only safe operations (column_mapping) are fully supported.
        Derived field expressions are restricted to simple arithmetic operations.
        """
        rule_type = rule.get("type")

        if rule_type == "column_mapping":
            source_col = rule.get("source_column")
            target_col = rule.get("target_column")
            mapping = rule.get("mapping", {})
            if source_col and target_col and source_col in df.columns:
                df[target_col] = df[source_col].map(mapping).fillna(df[source_col])
            else:
                logger.warning(
                    "Invalid column_mapping rule configuration or missing source column: "
                    f"source_column={source_col!r}, target_column={target_col!r}"
                )

        elif rule_type == "derived_field":
            target_col = rule.get("target_column")
            expression = rule.get("expression", "")
            if expression and target_col:
                # Only allow safe expressions using pandas eval with restricted operations
                # Allowed: column names, basic arithmetic (+, -, *, /)
                allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/(). ")
                if not all(c in allowed_chars for c in expression):
                    logger.warning(f"Unsafe characters in expression '{expression}', skipping rule")
                    return df
                # Check for any dangerous patterns
                dangerous_patterns = ["import", "exec", "eval", "compile", "__", "open", "file"]
                if any(pattern in expression.lower() for pattern in dangerous_patterns):
                    logger.warning(f"Dangerous pattern detected in expression '{expression}', skipping rule")
                    return df
                try:
                    df[target_col] = df.eval(expression)
                except Exception as e:
                    logger.warning(f"Failed to evaluate expression '{expression}': {e}")

        return df

    def _detect_outliers(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Detect and flag outliers in numeric columns.

        Methods:
        - 'iqr': Interquartile Range method
        - 'zscore': Z-score method

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame with outlier flags, metrics dict)
        """
        logger.info(f"Detecting outliers (method: {self.outlier_method})")

        if not self.outlier_enabled:
            return df, {"enabled": False}

        outlier_counts: Dict[str, int] = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Skip columns that shouldn't be checked for outliers
        skip_cols = {"loan_id", "id", "dpd"}  # DPD can legitimately be high
        check_cols = [col for col in numeric_cols if col not in skip_cols]

        for col in check_cols:
            if self.outlier_method == "iqr":
                outliers = self._detect_outliers_iqr(df[col])
            else:  # zscore
                outliers = self._detect_outliers_zscore(df[col])

            outlier_count = outliers.sum()
            if outlier_count > 0:
                outlier_flag_col = f"{col}_outlier"
                df[outlier_flag_col] = outliers
                outlier_counts[col] = int(outlier_count)
                logger.info(f"Found {outlier_count} outliers in column '{col}'")

        metrics = {
            "enabled": True,
            "method": self.outlier_method,
            "threshold": self.outlier_threshold,
            "columns_checked": len(check_cols),
            "outliers_detected": outlier_counts,
            "total_outlier_rows": sum(outlier_counts.values()),
        }

        return df, metrics

    def _detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """Detect outliers using IQR method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - self.outlier_threshold * IQR
        upper_bound = Q3 + self.outlier_threshold * IQR
        return (series < lower_bound) | (series > upper_bound)

    def _detect_outliers_zscore(self, series: pd.Series) -> pd.Series:
        """Detect outliers using Z-score method."""
        mean = series.mean()
        std = series.std()
        if std == 0:
            return pd.Series([False] * len(series), index=series.index)
        z_scores = np.abs((series - mean) / std)
        return z_scores > self.outlier_threshold

    def _check_referential_integrity(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Check referential integrity across entities.

        Validates:
        - Unique identifiers are actually unique
        - Foreign key relationships are valid
        - Required relationships exist

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (DataFrame, integrity metrics)
        """
        logger.info("Checking referential integrity")

        integrity_issues: List[Dict[str, Any]] = []

        # Check for unique loan_id if present
        if "loan_id" in df.columns:
            duplicates = df["loan_id"].duplicated().sum()
            if duplicates > 0:
                integrity_issues.append(
                    {
                        "type": "duplicate_primary_key",
                        "column": "loan_id",
                        "count": int(duplicates),
                    }
                )
                logger.warning(f"Found {duplicates} duplicate loan_id values")

        # Check for orphan records (borrower_id without valid reference)
        if "borrower_id" in df.columns:
            null_borrowers = df["borrower_id"].isnull().sum()
            if null_borrowers > 0:
                integrity_issues.append(
                    {
                        "type": "null_foreign_key",
                        "column": "borrower_id",
                        "count": int(null_borrowers),
                    }
                )

        # Check date consistency
        date_cols = [col for col in df.columns if col.endswith("_date")]
        if "origination_date" in date_cols and "due_date" in date_cols:
            if df["origination_date"].dtype == "datetime64[ns]" and df["due_date"].dtype == "datetime64[ns]":
                invalid_dates = (df["due_date"] < df["origination_date"]).sum()
                if invalid_dates > 0:
                    integrity_issues.append(
                        {
                            "type": "invalid_date_sequence",
                            "description": "due_date before origination_date",
                            "count": int(invalid_dates),
                        }
                    )

        # Check for negative amounts in columns that should be positive
        positive_cols = ["amount", "current_balance", "original_amount"]
        for col in positive_cols:
            if col in df.columns:
                # Filter out NaN values before checking for negatives
                valid_values = df[col].dropna()
                negative_count = (valid_values < 0).sum()
                if negative_count > 0:
                    integrity_issues.append(
                        {
                            "type": "negative_value",
                            "column": col,
                            "count": int(negative_count),
                        }
                    )

        metrics = {
            "checks_performed": 4,
            "issues_found": len(integrity_issues),
            "issues": integrity_issues,
            "integrity_status": "pass" if len(integrity_issues) == 0 else "warning",
        }

        if integrity_issues:
            logger.warning(f"Found {len(integrity_issues)} referential integrity issues")
        else:
            logger.info("Referential integrity checks passed")

        return df, metrics
