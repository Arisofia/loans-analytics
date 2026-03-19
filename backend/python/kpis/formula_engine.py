"""
KPI Formula Engine for parsing and executing SQL-like KPI formulas on DataFrames.
"""

import ast
import os
import re
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd

from backend.python.logging_config import get_logger

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
        formula = formula.strip()

        if self._is_comparison_formula(formula):
            return self._execute_comparison_formula(formula)
        if self._is_arithmetic_formula(formula):
            return self._execute_arithmetic_formula(formula)
        return self._execute_simple_formula(formula)

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

        try:
            return self._safe_eval_numeric_expression(expression)
        except ZeroDivisionError:
            logger.warning(
                "Comparison KPI formula hit division by zero; returning 0.0. "
                "formula=%s, context=%s",
                formula,
                context,
            )
            return Decimal("0.0")

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
            if right == 0:
                raise ZeroDivisionError("Division by zero in KPI formula")
            return left / right
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

        snapshot_date_candidates = [
            "measurement_date",
            "snapshot_date",
            "as_of_date",
            "reporting_date",
            "data_ingest_ts",
        ]
        date_column = next(
            (col for col in snapshot_date_candidates if col in self.df.columns), None
        )

        # Optional legacy fallback for environments that still rely on origination-based MoM.
        # Disabled by default to avoid misleading pre-ingesta "rotation" values.
        if date_column is None and os.getenv("KPI_ENGINE_ALLOW_ORIGINATION_FALLBACK", "0") == "1":
            fallback_candidates = [
                "origination_date",
                "disbursement_date",
                "last_payment_date",
                "maturity_date",
            ]
            date_column = next((col for col in fallback_candidates if col in self.df.columns), None)
        if date_column is None:
            logger.info(
                "Monthly comparison skipped: no snapshot date column found "
                "(set KPI_ENGINE_ALLOW_ORIGINATION_FALLBACK=1 to enable legacy fallback)."
            )
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
        return str(self._execute_simple_formula(match[0]))

    def _execute_simple_formula(self, formula: str) -> Decimal:
        """Execute simple aggregation formulas."""
        result = Decimal("0.0")
        agg_match = re.match(r"(SUM|AVG|COUNT)\((.+?)\)", formula, re.IGNORECASE)
        if not agg_match:
            return result

        agg_func = agg_match[1].upper()
        content = agg_match[2].strip()

        distinct = False
        if content.startswith("DISTINCT "):
            distinct = True
            content = content[9:].strip()

        if where_match := re.match(r"(.+?)\s+WHERE\s+(.+)", content, re.IGNORECASE):
            column = where_match[1].strip()
            condition = where_match[2].strip()
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
            condition = re.sub(r"\s+", " ", self._strip_outer_parentheses(condition).strip())
            if not condition:
                return self._false_mask()

            or_parts = self._split_logical_condition(condition, "OR")
            if len(or_parts) > 1:
                mask = self._false_mask()
                for part in or_parts:
                    mask = mask | self._build_where_mask(part)
                return mask.fillna(False).astype(bool)

            and_parts = self._split_logical_condition(condition, "AND")
            if len(and_parts) > 1:
                mask = self._true_mask()
                for part in and_parts:
                    mask = mask & self._build_where_mask(part)
                return mask.fillna(False).astype(bool)

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

        # Fail closed for malformed/unsupported predicates.
        return self._false_mask()

    @staticmethod
    def _strip_outer_parentheses(condition: str) -> str:
        """Strip redundant outer parentheses from a condition string."""
        trimmed = condition.strip()
        while trimmed.startswith("(") and trimmed.endswith(")"):
            depth = 0
            balanced = True
            for idx, ch in enumerate(trimmed):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                if depth == 0 and idx < len(trimmed) - 1:
                    balanced = False
                    break
            if not balanced or depth != 0:
                break
            trimmed = trimmed[1:-1].strip()
        return trimmed

    @staticmethod
    def _split_logical_condition(condition: str, operator: str) -> List[str]:
        """Split a condition by logical operator at top-level depth."""
        token = f" {operator.upper()} "
        normalized = condition
        upper = normalized.upper()
        parts: List[str] = []
        depth = 0
        start = 0
        i = 0

        while i < len(normalized):
            ch = normalized[i]
            if ch == "(":
                depth += 1
                i += 1
                continue
            if ch == ")" and depth > 0:
                depth -= 1
                i += 1
                continue
            if depth == 0 and upper.startswith(token, i):
                if part := normalized[start:i].strip():
                    parts.append(part)
                i += len(token)
                start = i
                continue
            i += 1

        if tail := normalized[start:].strip():
            parts.append(tail)
        return parts

    def _parse_in_condition(self, condition: str) -> Optional[pd.Series]:
        """Parse and evaluate an IN condition."""
        match = re.match(r"(.+?)\s+IN\s+\[(.+?)\]", condition, re.IGNORECASE)
        if not match:
            return None
        column = match[1].strip()
        if column not in self.df.columns:
            return self._false_mask()
        values = [value.strip().strip("'\"") for value in match[2].split(",")]
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
                return self._false_mask()
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
        mask = series != value if operator == "!=" else series == value
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
        # Use mixed-format parser when available to avoid noisy inference warnings
        # on heterogeneous real-world date columns.
        try:
            dt = pd.to_datetime(self.df[column], errors="coerce", format="mixed")
        except TypeError:
            # pandas versions without format='mixed'
            dt = pd.to_datetime(self.df[column], errors="coerce")
        self._datetime_cache[column] = dt
        return dt
