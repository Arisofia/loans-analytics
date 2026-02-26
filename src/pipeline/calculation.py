"""
PHASE 3: KPI CALCULATION

Responsibilities:
- Compute all KPIs from clean data
- Apply formulas with traceability
- Time-series rollups (daily/weekly/monthly)
- Anomaly detection
- Generate calculation manifest with lineage

NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/data/run_data_pipeline.py
"""

import ast
import json
import os
import re
import traceback
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from python.logging_config import get_logger

logger = get_logger(__name__)


class KPIFormulaEngine:
    """Engine for parsing and executing KPI formulas on DataFrames."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.month_start = pd.Timestamp.now().replace(day=1)
        self._where_cache: Dict[str, pd.Series] = {}
        self._numeric_cache: Dict[str, pd.Series] = {}
        self._datetime_cache: Dict[str, pd.Series] = {}
        self._polars_enabled = os.getenv("KPI_ENGINE_USE_POLARS", "1") == "1"

    def calculate(self, formula: str) -> Decimal:
        """Parse and execute a KPI formula."""
        try:
            formula = formula.strip()

            if self._is_comparison_formula(formula):
                return self._execute_comparison_formula(formula)
            if self._is_arithmetic_formula(formula):
                return self._execute_arithmetic_formula(formula)
            return self._execute_simple_formula(formula)
        except Exception as e:
            # Structured logging with full context
            logger.warning(
                "Formula execution failed",
                extra={
                    "formula": formula,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "dataframe_shape": self.df.shape,
                    "available_columns": list(self.df.columns),
                },
            )
            return Decimal("0.0")

    def _is_comparison_formula(self, formula: str) -> bool:
        """Check if formula compares two periods."""
        return "current_month" in formula or "previous_month" in formula

    def _is_arithmetic_formula(self, formula: str) -> bool:
        """Check if formula contains arithmetic operations between aggregations."""
        return any(op in formula for op in [" + ", " - ", " * ", " / "]) and "(" in formula

    def _execute_comparison_formula(self, formula: str) -> Decimal:
        """Execute formulas that compare period-level balance variables."""
        expression = formula
        context = self._build_comparison_context()

        for variable, value in context.items():
            expression = re.sub(rf"\b{re.escape(variable)}\b", str(value), expression)

        return self._safe_eval_numeric_expression(expression)

    def _safe_eval_numeric_expression(self, expression: str) -> Decimal:
        """
        Safely evaluate a numeric expression.

        Supported operations: +, -, *, /, parentheses, unary +/-.
        """
        parsed = ast.parse(expression, mode="eval")
        return self._eval_numeric_ast(parsed)

    def _eval_numeric_ast(self, node: ast.AST) -> Decimal:
        """Recursively evaluate supported numeric AST nodes."""
        if isinstance(node, ast.Expression):
            return self._eval_numeric_ast(node.body)
        if isinstance(node, ast.BinOp):
            left = self._eval_numeric_ast(node.left)
            right = self._eval_numeric_ast(node.right)
            return self._eval_binary_operation(node.op, left, right)
        if isinstance(node, ast.UnaryOp):
            value = self._eval_numeric_ast(node.operand)
            return self._eval_unary_operation(node.op, value)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")

    @staticmethod
    def _eval_binary_operation(operator: ast.AST, left: Decimal, right: Decimal) -> Decimal:
        """Evaluate a supported binary operation."""
        if isinstance(operator, ast.Add):
            return left + right
        if isinstance(operator, ast.Sub):
            return left - right
        if isinstance(operator, ast.Mult):
            return left * right
        if isinstance(operator, ast.Div):
            return Decimal("0.0") if right == 0 else left / right
        raise ValueError(f"Unsupported binary operator: {type(operator).__name__}")

    @staticmethod
    def _eval_unary_operation(operator: ast.AST, value: Decimal) -> Decimal:
        """Evaluate a supported unary operation."""
        if isinstance(operator, ast.UAdd):
            return value
        if isinstance(operator, ast.USub):
            return -value
        raise ValueError(f"Unsupported unary operator: {type(operator).__name__}")

    def _build_comparison_context(self) -> Dict[str, Decimal]:
        """
        Build comparison variables used by KPI formulas.

        Uses the most recent month present in the dataset as `current_month`.
        """
        current_balance, previous_balance = self._resolve_monthly_balances()
        return {
            "current_month_balance": current_balance,
            "previous_month_balance": previous_balance,
        }

    def _resolve_monthly_balances(self) -> tuple[Decimal, Decimal]:
        """
        Resolve current/previous month balances from the available loan tape.

        Returns:
            (current_month_balance, previous_month_balance)
        """
        if "outstanding_balance" not in self.df.columns:
            return Decimal("0.0"), Decimal("0.0")

        date_candidates = [
            "measurement_date",
            "snapshot_date",
            "as_of_date",
            "reporting_date",
            "origination_date",
            "disbursement_date",
            "last_payment_date",
            "maturity_date",
        ]
        date_column = next((col for col in date_candidates if col in self.df.columns), None)
        if date_column is None:
            return Decimal("0.0"), Decimal("0.0")

        if self._polars_enabled and len(self.df) >= 100_000:
            try:
                import polars as pl

                pl_df = pl.from_pandas(
                    self.df[[date_column, "outstanding_balance"]].copy()
                ).with_columns(
                    pl.col(date_column).cast(pl.Datetime, strict=False).alias("date"),
                    pl.col("outstanding_balance")
                    .cast(pl.Float64, strict=False)
                    .fill_null(0.0)
                    .alias("balance"),
                )
                pl_df = pl_df.select(["date", "balance"]).filter(pl.col("date").is_not_null())
                if pl_df.is_empty():
                    return Decimal("0.0"), Decimal("0.0")

                monthly = (
                    pl_df.with_columns(pl.col("date").dt.truncate("1mo").alias("month"))
                    .group_by("month")
                    .agg(pl.col("balance").sum().alias("balance_sum"))
                    .sort("month")
                )

                if monthly.height == 0:
                    return Decimal("0.0"), Decimal("0.0")

                month_to_balance = {
                    pd.Timestamp(row["month"]).to_period("M"): float(row["balance_sum"])
                    for row in monthly.select(["month", "balance_sum"]).to_dicts()
                }
                current_period = max(month_to_balance)
                previous_period = current_period - 1
                current_balance = Decimal(str(month_to_balance.get(current_period, 0.0)))
                previous_balance = Decimal(str(month_to_balance.get(previous_period, 0.0)))
                return current_balance, previous_balance
            except Exception as exc:
                logger.debug("Polars monthly balance path failed, falling back to pandas: %s", exc)

        period_df = pd.DataFrame(
            {
                "date": self._get_datetime_series(date_column),
                "balance": self._get_numeric_series("outstanding_balance").fillna(0.0),
            }
        ).dropna(subset=["date"])
        if period_df.empty:
            return Decimal("0.0"), Decimal("0.0")

        period_df["period"] = period_df["date"].dt.to_period("M")
        current_period = period_df["period"].max()
        previous_period = current_period - 1

        current_balance = Decimal(
            str(period_df.loc[period_df["period"] == current_period, "balance"].sum())
        )
        previous_balance = Decimal(
            str(period_df.loc[period_df["period"] == previous_period, "balance"].sum())
        )
        return current_balance, previous_balance

    def _execute_arithmetic_formula(self, formula: str) -> Decimal:
        """Execute formulas with arithmetic operations."""
        expression = re.sub(
            r"(SUM|AVG|COUNT)\([^)]+\)",
            self._replace_aggregation_match,
            formula,
            flags=re.IGNORECASE,
        )
        try:
            return self._safe_eval_numeric_expression(expression)
        except Exception as exc:
            logger.debug("Arithmetic formula evaluation failed for '%s': %s", formula, exc)
            return Decimal("0.0")

    def _replace_aggregation_match(self, match: re.Match) -> str:
        """Replace an aggregation fragment with its computed numeric value."""
        return str(self._execute_simple_formula(match.group(0)))

    def _execute_simple_formula(self, formula: str) -> Decimal:
        """Execute simple aggregation formulas."""
        result = Decimal("0.0")
        agg_match = re.match(r"(SUM|AVG|COUNT)\((.+?)\)", formula, re.IGNORECASE)
        if not agg_match:
            return result

        agg_func = agg_match.group(1).upper()
        content = agg_match.group(2).strip()

        distinct = False
        if content.startswith("DISTINCT "):
            distinct = True
            content = content[9:].strip()

        where_match = re.match(r"(.+?)\s+WHERE\s+(.+)", content, re.IGNORECASE)
        if where_match:
            column = where_match.group(1).strip()
            condition = where_match.group(2).strip()
            filtered_df = self._apply_where_clause(condition)
        else:
            column = content
            filtered_df = self.df

        if filtered_df.empty or column not in filtered_df.columns:
            if column not in filtered_df.columns:
                logger.debug("Column '%s' not found in data", column)
            return result

        if agg_func == "SUM":
            result = Decimal(str(filtered_df[column].sum()))
        elif agg_func == "AVG":
            result = Decimal(str(filtered_df[column].mean()))
        elif agg_func == "COUNT":
            result = Decimal(
                str(filtered_df[column].nunique() if distinct else filtered_df[column].count())
            )

        return result

    def _apply_where_clause(self, condition: str) -> pd.DataFrame:
        """Apply WHERE clause to filter DataFrame."""
        cached_mask = self._where_cache.get(condition)
        if cached_mask is not None:
            return self.df[cached_mask]

        mask = self._build_where_mask(condition)
        filtered_df = self.df[mask]
        self._cache_where_mask(condition, mask, filtered_df)
        return filtered_df

    def _build_where_mask(self, condition: str) -> pd.Series:
        """Build a boolean mask from a limited SQL-like WHERE clause."""
        try:
            in_mask = self._parse_in_condition(condition)
            if in_mask is not None:
                return in_mask

            for operator in (">=", "<=", "!=", ">", "<", "="):
                parsed = self._split_binary_condition(condition, operator)
                if parsed is None:
                    continue
                column, raw_value = parsed
                return self._build_binary_mask(column, operator, raw_value)

        except Exception as exc:
            logger.debug("WHERE clause failed: %s - %s", condition, str(exc))

        return self._true_mask()

    def _parse_in_condition(self, condition: str) -> Optional[pd.Series]:
        """Parse and evaluate an IN condition."""
        match = re.match(r"(.+?)\s+IN\s+\[(.+?)\]", condition, re.IGNORECASE)
        if not match:
            return None
        column = match.group(1).strip()
        if column not in self.df.columns:
            return self._false_mask()
        values = [value.strip().strip("'\"") for value in match.group(2).split(",")]
        return self.df[column].astype(str).isin(values).fillna(False).astype(bool)

    @staticmethod
    def _split_binary_condition(condition: str, operator: str) -> Optional[tuple[str, str]]:
        """Split a binary condition into column and value."""
        if operator not in condition:
            return None
        left, right = condition.split(operator, 1)
        return left.strip(), right.strip()

    def _build_binary_mask(self, column: str, operator: str, raw_value: str) -> pd.Series:
        """Build mask for a non-IN binary condition."""
        if column not in self.df.columns:
            return self._false_mask()

        if raw_value == "MONTH_START" and operator in {">=", "<=", ">", "<"}:
            return self._compare_datetime_to_month_start(column, operator)

        if operator in {">=", "<=", ">", "<"}:
            numeric_value = self._parse_numeric_literal(raw_value)
            if numeric_value is None:
                return self._true_mask()
            return self._compare_numeric(column, operator, numeric_value)

        return self._compare_string(column, operator, raw_value.strip("'\""))

    def _compare_datetime_to_month_start(self, column: str, operator: str) -> pd.Series:
        """Compare datetime column values against MONTH_START."""
        series = self._get_datetime_series(column)
        if operator == ">=":
            mask = series >= self.month_start
        elif operator == "<=":
            mask = series <= self.month_start
        elif operator == ">":
            mask = series > self.month_start
        else:
            mask = series < self.month_start
        return mask.fillna(False).astype(bool)

    def _compare_numeric(self, column: str, operator: str, value: float) -> pd.Series:
        """Compare numeric column values against a numeric threshold."""
        series = self._get_numeric_series(column)
        if operator == ">=":
            mask = series >= value
        elif operator == "<=":
            mask = series <= value
        elif operator == ">":
            mask = series > value
        else:
            mask = series < value
        return mask.fillna(False).astype(bool)

    def _compare_string(self, column: str, operator: str, value: str) -> pd.Series:
        """Compare stringified column values using equality/inequality."""
        series = self.df[column].astype(str)
        if operator == "!=":
            mask = series != value
        else:
            mask = series == value
        return mask.fillna(False).astype(bool)

    @staticmethod
    def _parse_numeric_literal(value: str) -> Optional[float]:
        """Parse numeric literal used in a WHERE expression."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _cache_where_mask(self, condition: str, mask: pd.Series, filtered_df: pd.DataFrame) -> None:
        """Cache WHERE clause masks for repeated formula use."""
        if len(filtered_df) < len(self.df):
            self._where_cache[condition] = mask.fillna(False).astype(bool)
            return
        self._where_cache[condition] = self._true_mask()

    def _true_mask(self) -> pd.Series:
        """Return a full True mask aligned to dataframe index."""
        return pd.Series(True, index=self.df.index, dtype=bool)

    def _false_mask(self) -> pd.Series:
        """Return a full False mask aligned to dataframe index."""
        return pd.Series(False, index=self.df.index, dtype=bool)

    def _get_numeric_series(self, column: str) -> pd.Series:
        """Get numeric series with one-time coercion cache."""
        cached = self._numeric_cache.get(column)
        if cached is not None:
            return cached
        numeric = pd.to_numeric(self.df[column], errors="coerce")
        self._numeric_cache[column] = numeric
        return numeric

    def _get_datetime_series(self, column: str) -> pd.Series:
        """Get datetime series with one-time coercion cache."""
        cached = self._datetime_cache.get(column)
        if cached is not None:
            return cached
        dt = pd.to_datetime(self.df[column], errors="coerce")
        self._datetime_cache[column] = dt
        return dt


class CalculationPhase:
    """Phase 3: KPI Calculation"""

    def __init__(self, config: Dict[str, Any], kpi_definitions: Dict[str, Any]):
        """
        Initialize calculation phase.

        Args:
            config: Calculation configuration from pipeline.yml
            kpi_definitions: KPI formulas from kpi_definitions.yaml
        """
        self.config = config
        self.kpi_definitions = kpi_definitions
        logger.info("Initialized calculation phase")

    def execute(
        self,
        clean_data_path: Optional[Path] = None,
        df: Optional[pd.DataFrame] = None,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute calculation phase.

        Args:
            clean_data_path: Path to clean data from Phase 2
            df: DataFrame (if already loaded)
            run_dir: Directory for this pipeline run

        Returns:
            Calculation results including KPI metrics
        """
        logger.info("Starting Phase 3: Calculation")

        try:
            # Load data
            if df is None:
                if clean_data_path and clean_data_path.exists():
                    df = pd.read_parquet(clean_data_path)
                else:
                    raise ValueError("No data provided for calculation")

            # Calculate KPIs
            kpi_results = self._calculate_kpis(df)

            # Time-series rollups
            time_series = self._calculate_time_series(df)

            # Anomaly detection
            anomalies = self._detect_anomalies(kpi_results)

            # Generate manifest
            manifest = self._generate_manifest(kpi_results, df)

            # Store results
            if run_dir:
                kpi_path = run_dir / "kpi_results.parquet"
                kpi_df = pd.DataFrame([kpi_results])
                kpi_df.to_parquet(kpi_path, index=False)

                manifest_path = run_dir / "calculation_manifest.json"

                with open(manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2, default=str)

                logger.info("Saved KPI results to %s", kpi_path)

            results = {
                "status": "success",
                "kpi_count": len(kpi_results),
                "kpis": kpi_results,
                "time_series": time_series,
                "anomalies": anomalies,
                "manifest": manifest,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("Calculation completed: %d KPIs computed", len(kpi_results))
            return results

        except Exception as e:
            traceback_str = traceback.format_exc()
            logger.error("Calculation failed: %s", str(e), exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback_str,
                "timestamp": datetime.now().isoformat(),
            }

    def _calculate_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all KPIs from definitions."""
        logger.info("Calculating KPIs")
        df = self._ensure_loan_count_column(df)
        engine = KPIFormulaEngine(df)
        kpis: Dict[str, Optional[Decimal]] = {}

        for category, kpi_name, formula in self._iter_kpi_formulas():
            kpis[kpi_name] = self._calculate_single_kpi(engine, category, kpi_name, formula)

        logger.info("Calculated %d KPIs", len(kpis))
        return kpis

    @staticmethod
    def _ensure_loan_count_column(df: pd.DataFrame) -> pd.DataFrame:
        """Add loan_count when borrower_id and loan_id exist."""
        if (
            "borrower_id" in df.columns
            and "loan_id" in df.columns
            and "loan_count" not in df.columns
        ):
            df = df.copy()
            df["loan_count"] = df.groupby("borrower_id")["loan_id"].transform("nunique")
        return df

    def _iter_kpi_formulas(self) -> List[tuple[str, str, str]]:
        """Collect (category, KPI name, formula) from configured KPI definitions."""
        category_order = [
            "portfolio_kpis",
            "asset_quality_kpis",
            "cash_flow_kpis",
            "growth_kpis",
            "customer_kpis",
            "operational_kpis",
        ]
        formulas: List[tuple[str, str, str]] = []
        for category in category_order:
            category_kpis = self.kpi_definitions.get(category, {})
            for kpi_name, kpi_config in category_kpis.items():
                formula = kpi_config.get("formula")
                if formula:
                    formulas.append((category, kpi_name, formula))
        return formulas

    def _calculate_single_kpi(
        self, engine: KPIFormulaEngine, category: str, kpi_name: str, formula: str
    ) -> Optional[Decimal]:
        """Calculate one KPI and return None on failure."""
        try:
            value = engine.calculate(formula)
            logger.debug("Calculated %s: %s", kpi_name, value)
            return value
        except Exception as exc:
            # Structured logging for KPI failures (traceability requirement)
            logger.warning(
                "KPI calculation failed",
                extra={
                    "kpi_name": kpi_name,
                    "category": category,
                    "formula": formula,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            return None

    def _calculate_time_series(self, df: pd.DataFrame) -> Dict[str, List]:
        """Calculate time-series rollups."""
        logger.info("Calculating time-series rollups")
        result = self._empty_time_series_result()
        date_columns = self._find_date_columns(df)

        if not date_columns:
            logger.debug("No date columns found for time-series analysis")
            return result

        date_col = date_columns[0]
        df_ts = self._prepare_time_series_dataframe(df, date_col)

        if df_ts.empty:
            return result

        numeric_cols = self._get_time_series_numeric_columns(df_ts)
        if not numeric_cols:
            return result

        result["daily"] = self._rollup_sum(df_ts, date_col, numeric_cols, "daily", 30)
        result["weekly"] = self._rollup_sum(df_ts, date_col, numeric_cols, "weekly", 12)
        result["monthly"] = self._rollup_sum(df_ts, date_col, numeric_cols, "monthly", 12)

        logger.info(
            "Time-series calculated: %d daily, %d weekly, %d monthly",
            len(result["daily"]),
            len(result["weekly"]),
            len(result["monthly"]),
        )
        return result

    @staticmethod
    def _empty_time_series_result() -> Dict[str, List[Dict[str, Any]]]:
        """Return empty result structure for time-series rollups."""
        return {"daily": [], "weekly": [], "monthly": []}

    def _find_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Find columns that can be interpreted as dates."""
        date_columns: List[str] = []
        for col in df.columns:
            if df[col].dtype not in ["datetime64[ns]", "object"]:
                continue
            try:
                parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
                if parsed.notna().any():
                    date_columns.append(col)
            except Exception as exc:
                logger.debug("Skipping non-date column %s: %s", col, exc)
        return date_columns

    @staticmethod
    def _prepare_time_series_dataframe(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Create clean dataframe with a parsed non-null date column."""
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        return df_ts.dropna(subset=[date_col])

    @staticmethod
    def _get_time_series_numeric_columns(df_ts: pd.DataFrame) -> List[str]:
        """Get numeric columns for rollups with fallback to amount."""
        numeric_cols = df_ts.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            return numeric_cols
        return ["amount"] if "amount" in df_ts.columns else []

    def _rollup_sum(
        self, df_ts: pd.DataFrame, date_col: str, numeric_cols: List[str], period: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Aggregate numeric columns by period and return record dictionaries."""
        try:
            if period == "daily":
                grouped = df_ts.groupby(df_ts[date_col].dt.date)[numeric_cols].sum()
            elif period == "weekly":
                grouped = df_ts.groupby(df_ts[date_col].dt.to_period("W"))[numeric_cols].sum()
            else:
                grouped = df_ts.groupby(df_ts[date_col].dt.to_period("M"))[numeric_cols].sum()
            return grouped.to_dict("records")[:limit]
        except Exception as exc:
            logger.warning(
                "%s rollup failed for %s: %s",
                period.capitalize(),
                date_col,
                exc,
                exc_info=True,
            )
            return []

    def _detect_anomalies(self, kpi_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in KPI values."""
        anomalies: List[Dict[str, Any]] = []

        try:
            normal_ranges = self._default_anomaly_ranges()

            for kpi_name, kpi_value in kpi_results.items():
                anomaly = self._build_anomaly_record(kpi_name, kpi_value, normal_ranges)
                if anomaly is None:
                    continue
                anomalies.append(anomaly)
                min_val, max_val = anomaly["expected_range"]
                logger.warning(
                    "Anomaly detected in %s: %s (expected: %s-%s)",
                    kpi_name,
                    anomaly["value"],
                    min_val,
                    max_val,
                )

            if anomalies:
                logger.info("Detected %d KPI anomalies", len(anomalies))

        except Exception as e:
            logger.error("Anomaly detection failed: %s", e, exc_info=True)

        return anomalies

    @staticmethod
    def _default_anomaly_ranges() -> Dict[str, tuple[float, float]]:
        """Expected KPI ranges in percentage units (30 means 30%)."""
        return {
            "par_30": (0, 30),
            "par_90": (0, 15),
            "default_rate": (0, 4),
            "portfolio_yield": (5, 15),
        }

    @staticmethod
    def _build_anomaly_record(
        kpi_name: str,
        kpi_value: Any,
        normal_ranges: Dict[str, tuple[float, float]],
    ) -> Optional[Dict[str, Any]]:
        """Return anomaly metadata if KPI value is outside expected range."""
        if kpi_value is None or not isinstance(kpi_value, (int, float)):
            return None
        if kpi_name not in normal_ranges:
            return None

        min_val, max_val = normal_ranges[kpi_name]
        if min_val <= kpi_value <= max_val:
            return None

        return {
            "kpi_name": kpi_name,
            "value": kpi_value,
            "expected_range": (min_val, max_val),
            "severity": "critical" if abs(kpi_value - max_val) > max_val * 0.5 else "warning",
        }

    def _generate_manifest(
        self, kpi_results: Dict[str, Any], source_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate calculation manifest with lineage."""
        return {
            "run_timestamp": datetime.now().isoformat(),
            "source_rows": len(source_df),
            "kpis_calculated": list(kpi_results.keys()),
            "formula_version": self.kpi_definitions.get("version", "unknown"),
            "traceability": {
                "source_columns": list(source_df.columns),
                "calculation_engine": "kpi_engine_v2",
            },
        }
