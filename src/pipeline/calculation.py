"""
PHASE 3: KPI CALCULATION

Responsibilities:
- Compute all KPIs from clean data
- Apply formulas with traceability
- Time-series rollups (daily/weekly/monthly)
- Anomaly detection
- Generate calculation manifest with lineage
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from python.logging_config import get_logger

logger = get_logger(__name__)


class KPIFormulaEngine:
    """Engine for parsing and executing KPI formulas on DataFrames."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.month_start = pd.Timestamp.now().replace(day=1)

    def calculate(self, formula: str) -> float:
        """Parse and execute a KPI formula."""
        try:
            formula = formula.strip()

            if self._is_comparison_formula(formula):
                return self._execute_comparison_formula(formula)
            elif self._is_arithmetic_formula(formula):
                return self._execute_arithmetic_formula(formula)
            else:
                return self._execute_simple_formula(formula)
        except Exception as e:
            logger.warning(f"Formula execution failed: {formula} - {str(e)}")
            return 0.0

    def _is_comparison_formula(self, formula: str) -> bool:
        """Check if formula compares two periods."""
        return "current_month" in formula or "previous_month" in formula

    def _is_arithmetic_formula(self, formula: str) -> bool:
        """Check if formula contains arithmetic operations between aggregations."""
        return any(op in formula for op in [" + ", " - ", " * ", " / "]) and "(" in formula

    def _execute_comparison_formula(self, formula: str) -> float:
        """Execute formulas that compare periods."""
        return 0.0

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
                    elif operator == "*" or operator == "* 100":
                        result = result * value
                    elif operator == "/" and value != 0:
                        result = result / value
                    operator = None
            elif part.replace(".", "").isdigit():
                value = float(part)
                if result is not None and operator:
                    if operator == "*" or operator == "* 100":
                        result = result * value
                    elif operator == "/" and value != 0:
                        result = result / value
                    operator = None

        return result if result is not None else 0.0

    def _execute_simple_formula(self, formula: str) -> float:
        """Execute simple aggregation formulas."""
        agg_match = re.match(r"(SUM|AVG|COUNT)\((.+?)\)", formula, re.IGNORECASE)
        if not agg_match:
            return 0.0

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

        if filtered_df.empty:
            return 0.0

        if column not in filtered_df.columns:
            logger.debug(f"Column '{column}' not found in data")
            return 0.0

        if agg_func == "SUM":
            return float(filtered_df[column].sum())
        elif agg_func == "AVG":
            return float(filtered_df[column].mean())
        elif agg_func == "COUNT":
            if distinct:
                return float(filtered_df[column].nunique())
            else:
                return float(filtered_df[column].count())

        return 0.0

    def _apply_where_clause(self, condition: str) -> pd.DataFrame:
        """Apply WHERE clause to filter DataFrame."""
        try:
            if ">=" in condition:
                parts = condition.split(">=")
                col = parts[0].strip()
                value = parts[1].strip()

                if value == "MONTH_START":
                    if col in self.df.columns:
                        return self.df[
                            pd.to_datetime(self.df[col], errors="coerce") >= self.month_start
                        ]
                elif value.isdigit():
                    if col in self.df.columns:
                        return self.df[self.df[col] >= int(value)]

            elif " IN " in condition:
                match = re.match(r"(.+?)\s+IN\s+\[(.+?)\]", condition, re.IGNORECASE)
                if match:
                    col = match.group(1).strip()
                    values = [v.strip().strip("'\"") for v in match.group(2).split(",")]
                    if col in self.df.columns:
                        return self.df[self.df[col].isin(values)]

            elif "!=" in condition:
                parts = condition.split("!=")
                col = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                if col in self.df.columns:
                    return self.df[self.df[col] != value]

            elif "=" in condition:
                parts = condition.split("=")
                col = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                if col in self.df.columns:
                    return self.df[self.df[col] == value]

        except Exception as e:
            logger.debug(f"WHERE clause failed: {condition} - {str(e)}")

        return self.df


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
                import json

                with open(manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2, default=str)

                logger.info(f"Saved KPI results to {kpi_path}")

            results = {
                "status": "success",
                "kpi_count": len(kpi_results),
                "kpis": kpi_results,
                "time_series": time_series,
                "anomalies": anomalies,
                "manifest": manifest,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Calculation completed: {len(kpi_results)} KPIs computed")
            return results

        except Exception as e:
            logger.error(f"Calculation failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _calculate_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all KPIs from definitions."""
        logger.info("Calculating KPIs")

        kpis = {}
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
                            logger.debug(f"Calculated {kpi_name}: {value}")
                        except Exception as e:
                            logger.warning(f"Failed to calculate {kpi_name}: {str(e)}")
                            kpis[kpi_name] = 0.0

        logger.info(f"Calculated {len(kpis)} KPIs")
        return kpis

    def _calculate_time_series(self, df: pd.DataFrame) -> Dict[str, List]:
        """Calculate time-series rollups."""
        logger.info("Calculating time-series rollups")

        date_columns = []
        for col in df.columns:
            if df[col].dtype in ["datetime64[ns]", "object"]:
                try:
                    pd.to_datetime(df[col], errors="raise")
                    date_columns.append(col)
                except Exception:
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
            except Exception:
                pass

            try:
                weekly = df_ts.groupby(df_ts[date_col].dt.to_period("W"))[numeric_cols].sum()
                result["weekly"] = weekly.to_dict("records")[:12]
            except Exception:
                pass

            try:
                monthly = df_ts.groupby(df_ts[date_col].dt.to_period("M"))[numeric_cols].sum()
                result["monthly"] = monthly.to_dict("records")[:12]
            except Exception:
                pass

        logger.info(
            f"Time-series calculated: {len(result['daily'])} daily, {len(result['weekly'])} weekly, {len(result['monthly'])} monthly"
        )
        return result

    def _detect_anomalies(self, kpi_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in KPI values."""
        # TODO: Implement anomaly detection
        # Compare against historical baselines
        return []

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
