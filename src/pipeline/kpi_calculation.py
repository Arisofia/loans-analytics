import importlib
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import yaml

from src.kpi_engine_v2 import KPIEngineV2
from src.pipeline.extended_kpis import ExtendedKPIGenerator
from src.pipeline.utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class CalculationResultV2:
    """Container for KPI calculation outputs and audit trail."""

    metrics: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]
    run_id: str
    timeseries: Dict[str, pd.DataFrame]
    anomalies: Dict[str, Any]
    timestamp: str
    extended_kpis: Optional[Dict[str, Any]] = None


class AnomalyDetector:
    """Handles detection of anomalies in KPI results compared to baseline."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def detect(self, metrics: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        anomaly_cfg = self.config.get("anomaly_detection", {})
        if not anomaly_cfg.get("enabled", False) or not baseline:
            return {}

        max_change = float(anomaly_cfg.get("max_change_pct", 0.2))
        anomalies: Dict[str, Any] = {}

        for name, metric in metrics.items():
            current = metric.get("value")
            prior = baseline.get(name, {}).get("value")
            if current is None or prior in (None, 0):
                continue
            change_pct = abs(current - prior) / abs(prior)
            if change_pct > max_change:
                anomalies[name] = {
                    "previous": prior,
                    "current": current,
                    "change_pct": round(change_pct, 4),
                }
        return anomalies


class MetricCalculator:
    """Handles individual metric and composite metric computations."""

    def __init__(self, config: Dict[str, Any], kpi_definitions: Dict[str, Any]):
        self.config = config
        self.kpi_definitions = kpi_definitions

    @staticmethod
    def import_function(dotted_path: str) -> Callable:
        module_path, func_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    def get_status(self, value: float, thresholds: Dict[str, List[float]]) -> str:
        if not thresholds:
            return "unknown"
        for status, bounds in thresholds.items():
            if len(bounds) == 2 and bounds[0] <= value <= bounds[1]:
                return status
        return "unknown"

    def compute_metric(
        self, df: pd.DataFrame, metric_cfg: Dict[str, Any], engine: Optional[KPIEngineV2] = None
    ) -> Dict[str, Any]:
        name = metric_cfg.get("name")
        ext_def = self.kpi_definitions.get("kpis", {}).get(name, {})

        func_path = metric_cfg.get("function") or ext_def.get("function")
        if not func_path:
            # Fallback to KPIEngineV2 direct calculation
            if not isinstance(name, str):
                raise ValueError(f"Invalid metric name for engine fallback: {name}")
            # Use provided engine or create a temporary one for this DF (e.g. for timeseries groups)
            calc_engine = engine if engine is not None else KPIEngineV2(df)
            val = calc_engine.get_metric(name)
            context = {"source": "KPIEngineV2"}
        else:
            func = self.import_function(func_path)
            val, context = func(df)

        value = float(val) if val is not None else None
        status = (
            self.get_status(value, ext_def.get("thresholds", {}))
            if value is not None
            else "unknown"
        )

        return {
            "value": value,
            "status": status,
            "display_name": ext_def.get("display_name", name),
            "formula": ext_def.get("formula") or metric_cfg.get("formula"),
            "source_table": metric_cfg.get("source_table"),
            "precision": ext_def.get("precision") or metric_cfg.get("precision"),
            "validation_range": ext_def.get("validation_range"),
            **context,
        }

    def compute_composite(
        self, base_metrics: Dict[str, Any], metric_cfg: Dict[str, Any]
    ) -> Dict[str, Any]:
        name = metric_cfg.get("name")
        func_path = metric_cfg.get("function")
        if not func_path:
            raise ValueError(f"Missing function for composite metric {name}")

        func = self.import_function(func_path)

        # Dynamic input resolution from config
        input_names = metric_cfg.get("inputs", ["PAR30", "CollectionRate"])
        inputs = []
        for inp in input_names:
            val = base_metrics.get(inp, {}).get("value")
            if val is None:
                logger.warning("Missing input %s for composite metric %s", inp, name)
                # We still try to proceed or we can raise, but letting it raise inside func
                # if it's strictly required is also an option.
            inputs.append(val)

        value, context = func(*inputs)
        return {
            "value": float(value) if value is not None else None,
            "formula": metric_cfg.get("formula"),
            "source_table": metric_cfg.get("source_table"),
            "precision": metric_cfg.get("precision"),
            "validation_range": metric_cfg.get("validation_range"),
            **context,
        }


class UnifiedCalculationV2:
    """Phase 3: KPI computation with enhanced traceability and consistent interfaces."""

    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None):
        self.config = config.get("pipeline", {}).get("phases", {}).get("calculation", {})
        self.run_id = run_id or f"calc_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []
        self.kpi_definitions = self._load_kpi_definitions()

        # Initialize specialized components
        self.calculator = MetricCalculator(self.config, self.kpi_definitions)
        self.anomalies = AnomalyDetector(self.config)

    def _load_kpi_definitions(self) -> Dict[str, Any]:
        config_path = Path("config/kpis/kpi_definitions.yaml")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as exc:
                logger.error("Failed to load KPI definitions: %s", exc)
        return {}

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": utc_now(),
            **details,
        }
        self.audit_log.append(entry)
        logger.info("[Calculation:%s] %s | %s", event, status, details)

    def _compute_timeseries(
        self, df: pd.DataFrame, metrics_cfg: List[Dict[str, Any]]
    ) -> Dict[str, pd.DataFrame]:
        ts_cfg = self.config.get("timeseries", {})
        if not ts_cfg.get("enabled", False):
            return {}
        time_column = ts_cfg.get("time_column")
        if not time_column or time_column not in df.columns:
            return {}

        df = df.copy()
        df[time_column] = pd.to_datetime(df[time_column], errors="coerce")
        df = df.dropna(subset=[time_column])
        rollups = ts_cfg.get("rollups", ["daily"])
        results: Dict[str, pd.DataFrame] = {}

        # Separate base and composite metrics for timeseries
        base_metrics_cfg = [m for m in metrics_cfg if not m.get("inputs")]
        comp_metrics_cfg = [m for m in metrics_cfg if m.get("inputs")]

        for rollup in rollups:
            freq_map = {"daily": "D", "weekly": "W", "monthly": "M"}
            freq = freq_map.get(rollup)
            if not freq:
                continue

            grouper = pd.Grouper(key=time_column, freq=freq)
            rows: List[Dict[str, Any]] = []

            for period, group in df.groupby(grouper):
                if pd.isna(period):
                    continue
                row = {"period_start": period}
                period_metrics: Dict[str, Any] = {}

                # 1. Base Metrics for period
                for metric in base_metrics_cfg:
                    name = metric.get("name")
                    if not name:
                        continue
                    try:
                        metric_result = self.calculator.compute_metric(group, metric)
                        row[name] = metric_result.get("value")
                        period_metrics[name] = metric_result
                    except Exception as exc:
                        row[name] = None
                        self._log_event(
                            "timeseries_metric_failed", "error", metric=name, error=str(exc)
                        )

                # 2. Composite Metrics for period
                for metric in comp_metrics_cfg:
                    name = metric.get("name")
                    if not name:
                        continue
                    try:
                        metric_result = self.calculator.compute_composite(period_metrics, metric)
                        row[name] = metric_result.get("value")
                    except Exception as exc:
                        row[name] = None
                        self._log_event(
                            "timeseries_composite_failed", "error", metric=name, error=str(exc)
                        )

                rows.append(row)
            results[rollup] = pd.DataFrame(rows)
        return results

    def calculate(
        self, df: pd.DataFrame, baseline_metrics: Optional[Dict[str, Any]] = None
    ) -> CalculationResultV2:
        self._log_event("start", "initiated", rows=len(df))

        metrics_cfg = list(self.config.get("metrics", []))
        metrics: Dict[str, Any] = {}
        kpi_engine = KPIEngineV2(df, actor="unified_pipeline", action="batch_calc")

        if df.empty:
            self._log_event("execution", "skipped", reason="Empty DataFrame")

        if not metrics_cfg:
            metrics = kpi_engine.calculate_all(include_composite=True)
        else:
            # Separate base and composite metrics based on configuration
            base_cfgs = [m for m in metrics_cfg if not m.get("inputs")]
            comp_cfgs = [m for m in metrics_cfg if m.get("inputs")]

            # 1. Base Metrics
            for metric_cfg in base_cfgs:
                name = metric_cfg.get("name")
                try:
                    metrics[name] = self.calculator.compute_metric(df, metric_cfg, engine=kpi_engine)
                    self._log_event("metric_computed", "success", metric=name)
                except Exception as exc:
                    self._log_event("metric_failed", "error", metric=name, error=str(exc))
                    metrics[name] = {"value": None, "error": str(exc)}

            # 2. Composite Metrics
            for metric_cfg in comp_cfgs:
                name = metric_cfg.get("name")
                try:
                    metrics[name] = self.calculator.compute_composite(metrics, metric_cfg)
                    self._log_event("metric_computed", "success", metric=name)
                except Exception as exc:
                    self._log_event("metric_failed", "error", metric=name, error=str(exc))
                    metrics[name] = {"value": None, "error": str(exc)}

        audit_trail = kpi_engine.get_audit_trail().to_dict(orient="records")
        timeseries = self._compute_timeseries(df, metrics_cfg)
        anomalies = self.anomalies.detect(metrics, baseline_metrics)

        extended_kpis = None
        try:
            generator = ExtendedKPIGenerator(df, metrics)
            extended_kpis = generator.generate(tier=3)
            self._log_event("extended_kpis_generated", "success", tier=3)
        except Exception as exc:
            self._log_event("extended_kpis_generation_failed", "warning", error=str(exc))

        self._log_event(
            "complete",
            "success",
            metric_count=len(metrics),
            audit_entries=len(audit_trail),
            anomaly_count=len(anomalies),
        )

        return CalculationResultV2(
            metrics=metrics,
            audit_trail=audit_trail,
            run_id=self.run_id,
            timeseries=timeseries,
            anomalies=anomalies,
            timestamp=utc_now(),
            extended_kpis=extended_kpis,
        )