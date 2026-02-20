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

    def calculate(self, formula: str) -> float:
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
            return 0.0

    def _is_comparison_formula(self, formula: str) -> bool:
        """Check if formula compares two periods."""
        return "current_month" in formula or "previous_month" in formula

    def _is_arithmetic_formula(self, formula: str) -> bool:
        """Check if formula contains arithmetic operations between aggregations."""
        return any(op in formula for op in [" + ", " - ", " * ", " / "]) and "(" in formula

    def _execute_comparison_formula(self, formula: str) -> float:
        """Execute formulas that compare period-level balance variables."""
        expression = formula
        context = self._build_comparison_context()

        for variable, value in context.items():
            expression = re.sub(rf"\b{re.escape(variable)}\b", str(value), expression)

        return self._safe_eval_numeric_expression(expression)

    def _safe_eval_numeric_expression(self, expression: str) -> float:
        """
        Safely evaluate a numeric expression.

        Supported operations: +, -, *, /, parentheses, unary +/-.
        """
        parsed = ast.parse(expression, mode="eval")

        def _eval(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                return _eval(node.body)

            if isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)

                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return 0.0 if right == 0 else left / right
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

            if isinstance(node, ast.UnaryOp):
                value = _eval(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return value
                if isinstance(node.op, ast.USub):
                    return -value
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)

            raise ValueError(f"Unsupported expression node: {type(node).__name__}")

        return float(_eval(parsed))

    def _build_comparison_context(self) -> Dict[str, float]:
        """
        Build comparison variables used by KPI formulas.

        Uses the most recent month present in the dataset as `current_month`.
        """
        current_balance, previous_balance = self._resolve_monthly_balances()
        return {
            "current_month_balance": current_balance,
            "previous_month_balance": previous_balance,
        }

    def _resolve_monthly_balances(self) -> tuple[float, float]:
        """
        Resolve current/previous month balances from the available loan tape.

        Returns:
            (current_month_balance, previous_month_balance)
        """
        if "outstanding_balance" not in self.df.columns:
            return 0.0, 0.0

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
            return 0.0, 0.0

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
                    return 0.0, 0.0

                monthly = (
                    pl_df.with_columns(pl.col("date").dt.truncate("1mo").alias("month"))
                    .group_by("month")
                    .agg(pl.col("balance").sum().alias("balance_sum"))
                    .sort("month")
                )

                if monthly.height == 0:
                    return 0.0, 0.0

                month_to_balance = {
                    pd.Timestamp(row["month"]).to_period("M"): float(row["balance_sum"])
                    for row in monthly.select(["month", "balance_sum"]).to_dicts()
                }
                current_period = max(month_to_balance)
                previous_period = current_period - 1
                current_balance = month_to_balance.get(current_period, 0.0)
                previous_balance = month_to_balance.get(previous_period, 0.0)
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
            return 0.0, 0.0

        period_df["period"] = period_df["date"].dt.to_period("M")
        current_period = period_df["period"].max()
        previous_period = current_period - 1

        current_balance = float(
            period_df.loc[period_df["period"] == current_period, "balance"].sum()
        )
        previous_balance = float(
            period_df.loc[period_df["period"] == previous_period, "balance"].sum()
        )
        return current_balance, previous_balance

    def _execute_arithmetic_formula(self, formula: str) -> float:
        """Execute formulas with arithmetic operations."""
        pattern = r"(SUM|AVG|COUNT)\([^)]+\)"
        parts = re.split(r"(\s*[\+\-\*/]\s*|\s*\*\s*100)", formula)

        result = None
        operator = None

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part in ["+", "-", "*", "/", "* 100"]:
                operator = part
            elif re.match(pattern, part):
                value = self._execute_simple_formula(part)

                if result is None:
                    result = value
                elif operator:
                    if operator == "+":
                        result = result + value
                    elif operator == "-":
                        result = result - value
                    elif operator in ("*", "* 100"):
                        result = result * value
                    elif operator == "/" and value != 0:
                        result = result / value
                    operator = None
            elif part.replace(".", "").isdigit():
                value = float(part)
                if result is not None and operator:
                    if operator in ("*", "* 100"):
                        result = result * value
                    elif operator == "/" and value != 0:
                        result = result / value
                    operator = None

        return result if result is not None else 0.0

    def _execute_simple_formula(self, formula: str) -> float:
        """Execute simple aggregation formulas."""
        result = 0.0
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
            result = float(filtered_df[column].sum())
        elif agg_func == "AVG":
            result = float(filtered_df[column].mean())
        elif agg_func == "COUNT":
            result = float(
                filtered_df[column].nunique() if distinct else filtered_df[column].count()
            )

        return result

    def _apply_where_clause(self, condition: str) -> pd.DataFrame:
        """Apply WHERE clause to filter DataFrame."""
        cached_mask = self._where_cache.get(condition)
        if cached_mask is not None:
            return self.df[cached_mask]

        filtered_df = self.df
        mask = pd.Series(True, index=self.df.index)

        try:
            if ">=" in condition:
                parts = condition.split(">=")
                col = parts[0].strip()
                value = parts[1].strip()

                if value == "MONTH_START":
                    if col in self.df.columns:
                        mask = self._get_datetime_series(col) >= self.month_start
                        filtered_df = self.df[mask.fillna(False)]
                    else:
                        filtered_df = self.df.iloc[:0]
                elif value.isdigit():
                    if col in self.df.columns:
                        mask = self._get_numeric_series(col) >= int(value)
                        filtered_df = self.df[mask.fillna(False)]
                    else:
                        filtered_df = self.df.iloc[:0]

            elif "<=" in condition:
                parts = condition.split("<=")
                col = parts[0].strip()
                value = parts[1].strip()
                if value.isdigit() or value.replace(".", "", 1).isdigit():
                    if col in self.df.columns:
                        mask = self._get_numeric_series(col) <= float(value)
                        filtered_df = self.df[mask.fillna(False)]
                    else:
                        filtered_df = self.df.iloc[:0]

            elif ">" in condition and "=" not in condition.replace(">=", ""):
                parts = condition.split(">")
                col = parts[0].strip()
                value = parts[1].strip()
                if value.isdigit() or value.replace(".", "", 1).isdigit():
                    if col in self.df.columns:
                        mask = self._get_numeric_series(col) > float(value)
                        filtered_df = self.df[mask.fillna(False)]
                    else:
                        filtered_df = self.df.iloc[:0]

            elif "<" in condition and "=" not in condition.replace("<=", ""):
                parts = condition.split("<")
                col = parts[0].strip()
                value = parts[1].strip()
                if value.isdigit() or value.replace(".", "", 1).isdigit():
                    if col in self.df.columns:
                        mask = self._get_numeric_series(col) < float(value)
                        filtered_df = self.df[mask.fillna(False)]
                    else:
                        filtered_df = self.df.iloc[:0]

            elif " IN " in condition:
                match = re.match(r"(.+?)\s+IN\s+\[(.+?)\]", condition, re.IGNORECASE)
                if match:
                    col = match.group(1).strip()
                    values = [v.strip().strip("'\"") for v in match.group(2).split(",")]
                    if col in self.df.columns:
                        mask = self.df[col].astype(str).isin(values)
                        filtered_df = self.df[mask.fillna(False)]
                    else:
                        filtered_df = self.df.iloc[:0]

            elif "!=" in condition:
                parts = condition.split("!=")
                col = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                if col in self.df.columns:
                    mask = self.df[col].astype(str) != value
                    filtered_df = self.df[mask.fillna(False)]
                else:
                    filtered_df = self.df.iloc[:0]

            elif "=" in condition:
                parts = condition.split("=")
                col = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                if col in self.df.columns:
                    mask = self.df[col].astype(str) == value
                    filtered_df = self.df[mask.fillna(False)]
                else:
                    filtered_df = self.df.iloc[:0]

        except Exception as e:
            logger.debug("WHERE clause failed: %s - %s", condition, str(e))

        if len(filtered_df) < len(self.df):
            self._where_cache[condition] = (
                pd.Series(self.df.index.isin(filtered_df.index), index=self.df.index)
                .fillna(False)
                .astype(bool)
            )
        else:
            self._where_cache[condition] = pd.Series(True, index=self.df.index, dtype=bool)

        return filtered_df

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

        # Derive columns needed by KPI formulas but not present in raw data
        if "borrower_id" in df.columns and "loan_id" in df.columns:
            if "loan_count" not in df.columns:
                df = df.copy()
                df["loan_count"] = df.groupby("borrower_id")["loan_id"].transform("nunique")

        kpis: Dict[str, Optional[float]] = {}
        engine = KPIFormulaEngine(df)

        kpi_categories = [
            "portfolio_kpis",
            "asset_quality_kpis",
            "cash_flow_kpis",
            "growth_kpis",
            "customer_kpis",
            "operational_kpis",
        ]

        for category in kpi_categories:
            if category in self.kpi_definitions:
                category_kpis = self.kpi_definitions[category]
                for kpi_name, kpi_config in category_kpis.items():
                    if "formula" in kpi_config:
                        try:
                            value = engine.calculate(kpi_config["formula"])
                            kpis[kpi_name] = value
                            logger.debug("Calculated %s: %s", kpi_name, value)
                        except Exception as e:
                            # Structured logging for KPI failures (traceability requirement)
                            logger.warning(
                                "KPI calculation failed",
                                extra={
                                    "kpi_name": kpi_name,
                                    "category": category,
                                    "formula": kpi_config.get("formula", "N/A"),
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )
                            kpis[kpi_name] = (
                                None  # Explicit None instead of 0.0 to indicate failure
                            )

        logger.info("Calculated %d KPIs", len(kpis))
        return kpis

    def _calculate_time_series(self, df: pd.DataFrame) -> Dict[str, List]:
        """Calculate time-series rollups."""
        logger.info("Calculating time-series rollups")

        date_columns = []
        for col in df.columns:
            if df[col].dtype in ["datetime64[ns]", "object"]:
                try:
                    parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
                    if parsed.notna().any():
                        date_columns.append(col)
                except Exception as e:
                    logger.debug("Skipping non-date column %s: %s", col, e)
                    continue

        if not date_columns:
            logger.debug("No date columns found for time-series analysis")
            return {"daily": [], "weekly": [], "monthly": []}

        date_col = date_columns[0]
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_col])

        if df_ts.empty:
            return {"daily": [], "weekly": [], "monthly": []}

        numeric_cols = df_ts.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            numeric_cols = ["amount"] if "amount" in df_ts.columns else []

        result: Dict[str, List[Dict[str, Any]]] = {"daily": [], "weekly": [], "monthly": []}

        if numeric_cols:
            try:
                daily = df_ts.groupby(df_ts[date_col].dt.date)[numeric_cols].sum()
                result["daily"] = daily.to_dict("records")[:30]
            except Exception as e:
                logger.warning("Daily rollup failed for %s: %s", date_col, e, exc_info=True)

            try:
                weekly = df_ts.groupby(df_ts[date_col].dt.to_period("W"))[numeric_cols].sum()
                result["weekly"] = weekly.to_dict("records")[:12]
            except Exception as e:
                logger.warning("Weekly rollup failed for %s: %s", date_col, e, exc_info=True)

            try:
                monthly = df_ts.groupby(df_ts[date_col].dt.to_period("M"))[numeric_cols].sum()
                result["monthly"] = monthly.to_dict("records")[:12]
            except Exception as e:
                logger.warning("Monthly rollup failed for %s: %s", date_col, e, exc_info=True)

        logger.info(
            "Time-series calculated: %d daily, %d weekly, %d monthly",
            len(result["daily"]),
            len(result["weekly"]),
            len(result["monthly"]),
        )
        return result

    def _detect_anomalies(self, kpi_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in KPI values."""
        anomalies = []

        try:
            # Define normal ranges for key KPIs (tuples: min, max)
            # Values are in PERCENTAGE units to match KPI engine output
            # (e.g., 30% = 30, not 0.30)
            normal_ranges = {
                "par_30": (0, 30),  # PAR-30 should be <30%
                "par_90": (0, 15),  # PAR-90 should be <15%
                "default_rate": (0, 4),  # Default rate <4%
                "portfolio_yield": (5, 15),  # Yield 5-15% (factoring)
            }

            for kpi_name, kpi_value in kpi_results.items():
                if kpi_value is None or not isinstance(kpi_value, (int, float)):
                    continue

                if kpi_name in normal_ranges:
                    min_val, max_val = normal_ranges[kpi_name]
                    if kpi_value < min_val or kpi_value > max_val:
                        anomalies.append(
                            {
                                "kpi_name": kpi_name,
                                "value": kpi_value,
                                "expected_range": (min_val, max_val),
                                "severity": (
                                    "critical"
                                    if abs(kpi_value - max_val) > max_val * 0.5
                                    else "warning"
                                ),
                            }
                        )
                        logger.warning(
                            "Anomaly detected in %s: %s (expected: %s-%s)",
                            kpi_name,
                            kpi_value,
                            min_val,
                            max_val,
                        )

            if anomalies:
                logger.info("Detected %d KPI anomalies", len(anomalies))

        except Exception as e:
            logger.error("Anomaly detection failed: %s", e, exc_info=True)

        return anomalies

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
