"""
PHASE 2: DATA TRANSFORMATION

Responsibilities:
- Data cleaning and normalization
- Null/outlier handling
- Type conversion
- Business rules application
- Referential integrity checks

NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/run_data_pipeline.py
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from python.logging_config import get_logger
from src.pipeline.utils import format_error_response

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
        "Current": "active",
        "current": "active",
        "CURRENT": "active",
        "Delinquent": "delinquent",
        "DELINQUENT": "delinquent",
        "Complete": "closed",
        "complete": "closed",
        "COMPLETE": "closed",
        "Closed": "closed",
        "CLOSED": "closed",
        "Default": "defaulted",
        "default": "defaulted",
        "DEFAULT": "defaulted",
        "Defaulted": "defaulted",
        "DEFAULTED": "defaulted",
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
        self.fill_values = null_config.get("fill_values", {"numeric": 0, "categorical": "unknown"})

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
            if df is None and raw_data_path and raw_data_path.exists():
                df = pd.read_parquet(raw_data_path)
            elif df is None:
                raise ValueError("No data provided for transformation")

            initial_rows = len(df)
            transformation_metrics: Dict[str, Any] = {}

            # Apply transformations with metrics tracking
            df = self._normalize_column_names(df)
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
                logger.info("Saved clean data to %s", output_path)
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

            logger.info("Transformation completed: %d → %d rows", initial_rows, len(df))
            return results

        except Exception as e:
            logger.error("Transformation failed: %s", str(e), exc_info=True)
            return format_error_response(e)

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to standard schema.
        Maps source-specific names to canonical pipeline names.
        """
        # Mapping: Source Name -> Canonical Name
        column_mapping = {
            "days_past_due": "dpd",
            "principal_amount": "amount",
            "current_status": "status",
            "loan_status": "status",
            "principal_balance": "current_balance",
            "loan_amount": "amount",
        }

        # Apply mapping for columns that exist in df
        rename_dict = {
            source: target
            for source, target in column_mapping.items()
            if source in df.columns and target not in df.columns
        }

        if rename_dict:
            df = df.rename(columns=rename_dict)
            logger.info("Renamed columns: %s", rename_dict)

        # Special case for outstanding_balance -> current_balance
        if "outstanding_balance" in df.columns:
            if "current_balance" not in df.columns:
                df = df.rename(columns={"outstanding_balance": "current_balance"})
                logger.info("Renamed outstanding_balance to current_balance")
            else:
                # If both exist, use outstanding_balance if current_balance is mostly zero/null
                null_or_zero = df["current_balance"].isna() | (df["current_balance"] == 0)
                if null_or_zero.mean() > 0.8:  # If more than 80% are zero/null
                    df["current_balance"] = df["outstanding_balance"]
                    logger.info(
                        "Overwrote current_balance with outstanding_balance "
                        "(due to high null/zero rate)"
                    )

        return df

    def _handle_nulls(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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
        logger.info("Handling null values (strategy: %s)", self.null_strategy)

        initial_nulls = df.isnull().sum()
        total_nulls = initial_nulls.sum()
        null_columns = initial_nulls[initial_nulls > 0].to_dict()

        if total_nulls == 0:
            logger.info("No null values found")
            return df, {"total_nulls": 0, "strategy_applied": "none", "columns_affected": []}

        metrics = self._create_null_metrics(total_nulls, null_columns)
        df, strategy_metrics = self._apply_null_strategy(df, null_columns)
        metrics.update(strategy_metrics)

        final_nulls = df.isnull().sum().sum()
        metrics["final_total_nulls"] = int(final_nulls)

        return df, metrics

    def _create_null_metrics(
        self, total_nulls: int, null_columns: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create initial metrics for null handling."""
        return {
            "initial_total_nulls": int(total_nulls),
            "null_columns": null_columns,
            "strategy_applied": self.null_strategy,
            "columns_affected": list(null_columns.keys()),
        }

    def _apply_null_strategy(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply the configured null handling strategy using strategy dispatch."""
        strategy_handlers = {
            "drop": lambda: self._apply_drop_strategy(df),
            "fill": lambda: self._apply_fill_strategy(df),
            "smart": lambda: self._smart_null_handling(df, null_columns),
        }
        handler = strategy_handlers.get(self.null_strategy)
        if handler:
            return handler()
        return df, {}

    def _apply_drop_strategy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply drop strategy for null handling."""
        rows_before = len(df)
        df = df.dropna()
        rows_dropped = rows_before - len(df)
        logger.info("Dropped %d rows with null values", rows_dropped)
        return df, {"rows_dropped": rows_dropped}

    def _apply_fill_strategy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply fill strategy for null handling."""
        df = self._fill_nulls_by_type(df)
        logger.info("Filled null values with configured defaults")
        return df, {"fill_values_used": self.fill_values}

    def _fill_nulls_by_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill nulls based on column data type."""
        for col in df.columns:
            if df[col].isnull().any() and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(self.fill_values.get("numeric", 0))
            elif df[col].isnull().any():
                df[col] = df[col].fillna(self.fill_values.get("categorical", "unknown"))
        return df

    def _smart_null_handling(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intelligent null handling based on null percentage and column importance.

        Uses configurable thresholds:
        - < LOW_NULL_THRESHOLD_PCT: Fill with median (numeric) or mode (categorical)
        - LOW to HIGH_NULL_THRESHOLD_PCT: Fill with missing indicator
        - > HIGH_NULL_THRESHOLD_PCT: Log warning, fill with default
        """
        total_rows = len(df)
        actions = self._process_null_columns(df, null_columns, total_rows)
        return df, {"smart_actions": actions}

    def _process_null_columns(
        self, df: pd.DataFrame, null_columns: Dict[str, int], total_rows: int
    ) -> Dict[str, str]:
        """Process null values for each column based on column type."""
        actions: Dict[str, str] = {}
        for col, null_count in null_columns.items():
            null_pct = null_count / total_rows * 100
            action = (
                self._handle_numeric_nulls(df, col, null_pct)
                if pd.api.types.is_numeric_dtype(df[col])
                else self._handle_categorical_nulls(df, col, null_pct)
            )
            actions[col] = action
        return actions

    def _handle_numeric_nulls(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        """Apply numeric null handling strategy for a column."""
        if null_pct < self.LOW_NULL_THRESHOLD_PCT:
            return self._fill_numeric_with_median(df, col)
        if null_pct < self.HIGH_NULL_THRESHOLD_PCT:
            return self._fill_numeric_with_indicator(df, col)
        return self._fill_numeric_with_zero(df, col, null_pct)

    def _fill_numeric_with_median(self, df: pd.DataFrame, col: str) -> str:
        """Fill numeric nulls with median value."""
        median_val = df[col].median()
        if pd.isna(median_val):
            median_val = 0
        df[col] = df[col].fillna(median_val)
        return f"filled_median ({median_val:.2f})"

    def _fill_numeric_with_indicator(self, df: pd.DataFrame, col: str) -> str:
        """Fill numeric nulls with missing indicator."""
        df[col] = df[col].fillna(self.MISSING_NUMERIC_INDICATOR)
        return f"filled_missing_indicator ({self.MISSING_NUMERIC_INDICATOR})"

    def _fill_numeric_with_zero(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        """Fill numeric nulls with zero for high null percentage columns."""
        df[col] = df[col].fillna(0)
        logger.warning("Column '%s' has %.1f%% nulls", col, null_pct)
        return f"filled_zero (high_null: {null_pct:.1f}%)"

    def _handle_categorical_nulls(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        """Apply categorical null handling strategy for a column."""
        if null_pct < self.LOW_NULL_THRESHOLD_PCT:
            return self._fill_categorical_with_mode(df, col)
        return self._fill_categorical_with_missing(df, col)

    def _fill_categorical_with_mode(self, df: pd.DataFrame, col: str) -> str:
        """Fill categorical nulls with mode value."""
        mode_val = df[col].mode()
        fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
        df[col] = df[col].fillna(fill_val)
        return f"filled_mode ({fill_val})"

    def _fill_categorical_with_missing(self, df: pd.DataFrame, col: str) -> str:
        """Fill categorical nulls with missing label."""
        df[col] = df[col].fillna("missing")
        return "filled_missing_label"

    def _normalize_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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

        self._normalize_date_columns(df, conversions)
        self._normalize_numeric_columns(df, conversions)
        self._normalize_status_column(df, conversions)

        metrics = {
            "enabled": True,
            "conversions_applied": len(conversions),
            "conversion_details": conversions,
        }

        logger.info("Applied %d type conversions", len(conversions))
        return df, metrics

    def _normalize_date_columns(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        """Normalize date columns to datetime."""
        for col in df.columns:
            if (col in self.DATE_COLUMNS or col.endswith("_date")) and (
                pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object"
            ):
                try:
                    df[col] = pd.to_datetime(df[col], format=self.date_format, errors="coerce")
                    conversions[col] = {"from": "string", "to": "datetime64"}
                except Exception as e:
                    logger.warning("Could not convert %s to datetime: %s", col, e)

    def _normalize_numeric_columns(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        """Normalize numeric columns to numeric dtype."""
        for col in df.columns:
            if col in self.NUMERIC_COLUMNS or any(
                kw in col.lower() for kw in ["amount", "balance", "rate", "count", "dpd"]
            ):
                if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
                    try:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                        conversions[col] = {"from": "string", "to": "numeric"}
                    except Exception as e:
                        logger.warning("Could not convert %s to numeric: %s", col, e)

    def _normalize_status_column(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        """Normalize status values to standardized labels."""
        if "status" not in df.columns:
            return
        original_values = df["status"].unique().tolist()
        df["status"] = df["status"].map(
            lambda x: self.STATUS_MAPPINGS.get(x, str(x).lower() if pd.notna(x) else x)
        )
        conversions["status"] = {"normalized_values": original_values}

    def _apply_business_rules(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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

        self._apply_dpd_bucket_rule(df, rules_applied, fields_created)
        self._apply_risk_category_rule(df, rules_applied, fields_created)
        self._apply_amount_tier_rule(df, rules_applied, fields_created)
        self._apply_custom_rules(df, rules_applied)

        metrics = {
            "rules_applied": len(rules_applied),
            "rule_names": rules_applied,
            "fields_created": fields_created,
        }

        logger.info("Applied %d business rules", len(rules_applied))
        return df, metrics

    def _apply_dpd_bucket_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """Apply DPD bucket assignment."""
        if "dpd" not in df.columns:
            return

        # Ensure dpd column is numeric (handle both float and Decimal types)
        if not pd.api.types.is_numeric_dtype(df["dpd"]):
            df["dpd"] = pd.to_numeric(df["dpd"], errors="coerce")

        df["dpd_bucket"] = pd.cut(
            df["dpd"],
            bins=[-np.inf, -0.001, 0.001, 30, 60, 90, 180, np.inf],
            labels=["unknown", "current", "1-29", "30-59", "60-89", "90-179", "180+"],
            include_lowest=True,
        ).astype(str)
        df.loc[df["dpd"].isna(), "dpd_bucket"] = "unknown"
        fields_created.append("dpd_bucket")
        rules_applied.append("dpd_bucket_assignment")

    def _apply_risk_category_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """Apply risk categorization rule."""
        if "status" in df.columns and "dpd" in df.columns:
            df["risk_category"] = df.apply(self._calculate_risk_category, axis=1)
            fields_created.append("risk_category")
            rules_applied.append("risk_categorization")

    def _apply_amount_tier_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """Apply amount tier classification rule."""
        if "amount" not in df.columns:
            return
        self._categorize_amount_tiers(df)
        self._record_applied_rule(rules_applied, fields_created)

    def _record_applied_rule(self, rules_applied: List[str], fields_created: List[str]) -> None:
        """Record that amount tier rule was applied."""
        fields_created.append("amount_tier")
        rules_applied.append("amount_tier_classification")

    def _categorize_amount_tiers(self, df: pd.DataFrame) -> None:
        """Categorize amounts into tiers using binning."""
        # Ensure amount column is numeric (handle both float and Decimal types)
        if not pd.api.types.is_numeric_dtype(df["amount"]):
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        df["amount_tier"] = pd.cut(
            df["amount"],
            bins=[-np.inf, 0, 5000, 25000, 100000, 500000, np.inf],
            labels=["invalid", "micro", "small", "medium", "large", "jumbo"],
            right=False,
        ).astype(str)
        df.loc[df["amount"].isna(), "amount_tier"] = "invalid"

    def _apply_custom_rules(self, df: pd.DataFrame, rules_applied: List[str]) -> None:
        """Apply custom business rules from configuration."""
        custom_rules = self.business_rules.get("transformations", [])
        for rule in custom_rules:
            try:
                df, success = self._apply_custom_rule(df, rule)
                if success:
                    rules_applied.append(rule.get("name", "unnamed_rule"))
            except Exception as e:
                logger.warning("Failed to apply custom rule: %s", e)

    def _assign_dpd_bucket(self, dpd: float) -> str:
        """Assign DPD (Days Past Due) bucket."""
        if pd.isna(dpd) or dpd < 0:
            bucket = "unknown"
        elif dpd == 0:
            bucket = "current"
        elif dpd < 30:
            bucket = "1-29"
        elif dpd < 60:
            bucket = "30-59"
        elif dpd < 90:
            bucket = "60-89"
        elif dpd < 180:
            bucket = "90-179"
        else:
            bucket = "180+"
        return bucket

    def _calculate_risk_category(self, row: pd.Series) -> str:
        """Calculate risk category based on status and DPD."""
        status = row.get("status", "")
        dpd = row.get("dpd", 0)

        if status == "defaulted":
            category = "critical"
        elif status == "delinquent" or (pd.notna(dpd) and dpd >= 90):
            category = "high"
        elif pd.notna(dpd) and dpd >= 30:
            category = "medium"
        elif status == "active" and (pd.isna(dpd) or dpd < 30):
            category = "low"
        else:
            category = "unknown"
        return category

    def _assign_amount_tier(self, amount: float) -> str:
        """Assign loan amount tier."""
        if pd.isna(amount) or amount <= 0:
            tier = "invalid"
        elif amount < 5000:
            tier = "micro"
        elif amount < 25000:
            tier = "small"
        elif amount < 100000:
            tier = "medium"
        elif amount < 500000:
            tier = "large"
        else:
            tier = "jumbo"
        return tier

    def _apply_custom_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        """
        Apply a custom business rule from configuration.

        Note: Only safe operations (column_mapping) are fully supported.
        Derived field expressions are restricted to simple arithmetic operations.

        Returns:
            Tuple of (DataFrame, success_flag) where success_flag indicates if rule was applied.
        """
        rule_type = rule.get("type")

        if rule_type == "column_mapping":
            return self._apply_column_mapping_rule(df, rule)
        if rule_type == "derived_field":
            return self._apply_derived_field_rule(df, rule)

        return df, False

    def _apply_column_mapping_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        """Apply a column mapping custom rule."""
        source_col = rule.get("source_column")
        target_col = rule.get("target_column")
        mapping = rule.get("mapping", {})
        if source_col and target_col and source_col in df.columns:
            df[target_col] = df[source_col].map(mapping).fillna(df[source_col])
            return df, True

        logger.warning(
            "Invalid column_mapping rule configuration or missing source column: "
            f"source_column={source_col!r}, target_column={target_col!r}"
        )
        return df, False

    def _apply_derived_field_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        """Apply a derived field custom rule with safety checks."""
        target_col = rule.get("target_column")
        expression = rule.get("expression", "")
        if not expression or not target_col:
            return df, False

        if not self._is_safe_expression(expression):
            return df, False

        try:
            df[target_col] = df.eval(expression)
            return df, True
        except Exception as e:
            logger.warning("Failed to evaluate expression '%s': %s", expression, e)
            return df, False

    def _is_safe_expression(self, expression: str) -> bool:
        """Validate that an expression is safe for pandas eval."""
        if not self._check_allowed_chars(expression):
            return False
        if self._check_dangerous_patterns(expression):
            return False
        return True

    def _check_allowed_chars(self, expression: str) -> bool:
        """Verify expression contains only allowed characters."""
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/(). "
        )
        if not all(c in allowed_chars for c in expression):
            logger.warning("Unsafe characters in expression '%s', skipping rule", expression)
            return False
        return True

    def _check_dangerous_patterns(self, expression: str) -> bool:
        """Check for dangerous patterns in expression."""
        dangerous_patterns = [
            "import",
            "exec",
            "eval",
            "compile",
            "__import__",
            "__builtins__",
            "__class__",
            "__getattr__",
            "__setattr__",
            "open",
            "file",
        ]
        expression_lower = expression.lower()
        if any(pattern in expression_lower for pattern in dangerous_patterns):
            logger.warning(
                "Dangerous pattern detected in expression '%s', skipping rule", expression
            )
            return True
        return False

    def _detect_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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
        logger.info("Detecting outliers (method: %s)", self.outlier_method)

        if not self.outlier_enabled:
            return df, {"enabled": False}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        skip_cols = {"loan_id", "id", "dpd"}
        check_cols = [col for col in numeric_cols if col not in skip_cols]

        df, outlier_counts = self._flag_outliers(df, check_cols)
        metrics = self._create_outlier_metrics(check_cols, outlier_counts)

        return df, metrics

    def _flag_outliers(
        self, df: pd.DataFrame, check_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Detect and flag outliers in specified columns."""
        outlier_counts: Dict[str, int] = {}

        for col in check_cols:
            outliers = (
                self._detect_outliers_iqr(df[col])
                if self.outlier_method == "iqr"
                else self._detect_outliers_zscore(df[col])
            )
            outlier_count = outliers.sum()
            if outlier_count > 0:
                self._record_outlier_flag(df, col, outliers, outlier_counts)

        return df, outlier_counts

    def _record_outlier_flag(
        self,
        df: pd.DataFrame,
        col: str,
        outliers: pd.Series,
        outlier_counts: Dict[str, int],
    ) -> None:
        """Record outlier flag for a column."""
        outlier_count = int(outliers.sum())
        outlier_flag_col = f"{col}_outlier"
        df[outlier_flag_col] = outliers
        outlier_counts[col] = outlier_count
        logger.info("Found %d outliers in column '%s'", outlier_count, col)

    def _create_outlier_metrics(
        self, check_cols: List[str], outlier_counts: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create metrics dictionary for outlier detection results."""
        return {
            "enabled": True,
            "method": self.outlier_method,
            "threshold": self.outlier_threshold,
            "columns_checked": len(check_cols),
            "outliers_detected": outlier_counts,
            "total_outlier_rows": sum(outlier_counts.values()),
        }

    def _detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """Detect outliers using IQR method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        # Handle edge case where there is no spread in the data; avoid flagging
        # any tiny deviation as an outlier when Q1 == Q3.
        if IQR == 0 or np.isclose(IQR, 0):
            return pd.Series([False] * len(series), index=series.index)
        lower_bound = Q1 - self.outlier_threshold * IQR
        upper_bound = Q3 + self.outlier_threshold * IQR
        return ((series < lower_bound) | (series > upper_bound)).fillna(False)

    def _detect_outliers_zscore(self, series: pd.Series) -> pd.Series:
        """Detect outliers using Z-score method."""
        # Work on non-null values to avoid NaN propagation in statistics and flags
        non_null = series.dropna()

        # If there are no non-null values or no variation, there can be no outliers
        if non_null.empty or non_null.std() == 0:
            return pd.Series(False, index=series.index)

        mean = non_null.mean()
        std = non_null.std()

        z_scores = np.abs((non_null - mean) / std)
        outliers_non_null = z_scores > self.outlier_threshold

        # Initialize all values as non-outliers and set only non-null outliers to True
        outliers = pd.Series(False, index=series.index)
        outliers.loc[non_null.index] = outliers_non_null.fillna(False)
        return outliers

    def _check_referential_integrity(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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
        self._check_primary_key_integrity(df, integrity_issues)
        self._check_foreign_key_integrity(df, integrity_issues)
        self._check_date_consistency(df, integrity_issues)
        self._check_positive_amounts(df, integrity_issues)

        metrics = {
            "checks_performed": 4,
            "issues_found": len(integrity_issues),
            "issues": integrity_issues,
            "integrity_status": "pass" if len(integrity_issues) == 0 else "warning",
        }

        if integrity_issues:
            logger.warning("Found %d referential integrity issues", len(integrity_issues))
        else:
            logger.info("Referential integrity checks passed")

        return df, metrics

    def _check_primary_key_integrity(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check for duplicate primary keys (loan_id)."""
        if "loan_id" not in df.columns:
            return

        duplicates = df["loan_id"].duplicated().sum()
        if duplicates > 0:
            integrity_issues.append(
                {
                    "type": "duplicate_primary_key",
                    "column": "loan_id",
                    "count": int(duplicates),
                }
            )
            logger.warning("Found %d duplicate loan_id values", duplicates)

    def _check_foreign_key_integrity(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check for orphan records with null foreign keys."""
        if "borrower_id" not in df.columns:
            return

        null_borrowers = df["borrower_id"].isnull().sum()
        if null_borrowers > 0:
            integrity_issues.append(
                {
                    "type": "null_foreign_key",
                    "column": "borrower_id",
                    "count": int(null_borrowers),
                }
            )

    def _check_date_consistency(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check date consistency (due_date should not be before origination_date)."""
        date_cols = [col for col in df.columns if col.endswith("_date")]
        has_both_dates = (
            "origination_date" in date_cols
            and "due_date" in date_cols
            and df["origination_date"].dtype == "datetime64[ns]"
            and df["due_date"].dtype == "datetime64[ns]"
        )

        if not has_both_dates:
            return

        valid_mask = df["due_date"].notna() & df["origination_date"].notna()
        invalid_dates = (
            df.loc[valid_mask, "due_date"] < df.loc[valid_mask, "origination_date"]
        ).sum()
        if invalid_dates > 0:
            integrity_issues.append(
                {
                    "type": "invalid_date_sequence",
                    "description": "due_date before origination_date",
                    "count": int(invalid_dates),
                }
            )

    def _check_positive_amounts(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check for negative amounts in columns that should be positive."""
        positive_cols = ["amount", "current_balance", "original_amount"]
        for col in positive_cols:
            if col not in df.columns:
                continue

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
