import importlib
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from python.kpi_engine_v2 import KPIEngineV2
from python.pipeline.utils import utc_now

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


class UnifiedCalculationV2:
    """Phase 3: KPI computation with enhanced traceability and consistent interfaces."""

    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None):
        self.config = config.get("pipeline", {}).get("phases", {}).get("calculation", {})
        self.run_id = run_id or f"calc_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []

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

    def _import_function(self, dotted_path: str):
        module_path, func_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    def _compute_metric(self, df: pd.DataFrame, metric_cfg: Dict[str, Any]) -> Dict[str, Any]:
        name = metric_cfg.get("name")
        func_path = metric_cfg.get("function")
        if not func_path:
            raise ValueError(f"Missing function for metric {name}")
        func = self._import_function(func_path)
        value, context = func(df)  # type: ignore[misc]
        return {
            "value": float(value) if value is not None else None,
            "formula": metric_cfg.get("formula"),
            "source_table": metric_cfg.get("source_table"),
            "precision": metric_cfg.get("precision"),
            "validation_range": metric_cfg.get("validation_range"),
            **context,
        }

    def _compute_composite(
        self, base_metrics: Dict[str, Any], metric_cfg: Dict[str, Any]
    ) -> Dict[str, Any]:
        name = metric_cfg.get("name")
        func_path = metric_cfg.get("function")
        if not func_path:
            raise ValueError(f"Missing function for composite metric {name}")
        func = self._import_function(func_path)
        par_val = base_metrics.get("PAR30", {}).get("value")
        coll_val = base_metrics.get("CollectionRate", {}).get("value")
        if par_val is None or coll_val is None:
            raise ValueError(f"Missing inputs for composite metric {name}")
        value, context = func(par_val, coll_val)  # type: ignore[misc]
        return {
            "value": float(value) if value is not None else None,
            "formula": metric_cfg.get("formula"),
            "source_table": metric_cfg.get("source_table"),
            "precision": metric_cfg.get("precision"),
            "validation_range": metric_cfg.get("validation_range"),
            **context,
        }

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

        for rollup in rollups:
            if rollup == "daily":
                grouper = pd.Grouper(key=time_column, freq="D")
            elif rollup == "weekly":
                grouper = pd.Grouper(key=time_column, freq="W")
            elif rollup == "monthly":
                grouper = pd.Grouper(key=time_column, freq="M")
            else:
                continue

            rows: List[Dict[str, Any]] = []
            for period, group in df.groupby(grouper):
                if pd.isna(period):
                    continue
                row = {"period_start": period}
                for metric in metrics_cfg:
                    name = metric.get("name")
                    if not name or name in {"PortfolioHealth", "HealthScore"}:
                        continue
                    try:
                        metric_result = self._compute_metric(group, metric)
                        row[name] = metric_result.get("value")
                    except Exception as exc:
                        row[name] = None
                        self._log_event(
                            "timeseries_metric_failed", "error", metric=name, error=str(exc)
                        )
                rows.append(row)
            results[rollup] = pd.DataFrame(rows)
        return results

    def _detect_anomalies(
        self, metrics: Dict[str, Any], baseline: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
            for metric_cfg in metrics_cfg:
                name = metric_cfg.get("name")
                if name in {"PortfolioHealth", "HealthScore"}:
                    continue
                try:
                    metrics[name] = self._compute_metric(df, metric_cfg)
                    self._log_event("metric_computed", "success", metric=name)
                except Exception as exc:
                    self._log_event("metric_failed", "error", metric=name, error=str(exc))
                    metrics[name] = {"value": None, "error": str(exc)}

            for metric_cfg in metrics_cfg:
                name = metric_cfg.get("name")
                if name not in {"PortfolioHealth", "HealthScore"}:
                    continue
                try:
                    metrics[name] = self._compute_composite(metrics, metric_cfg)
                    self._log_event("metric_computed", "success", metric=name)
                except Exception as exc:
                    self._log_event("metric_failed", "error", metric=name, error=str(exc))
                    metrics[name] = {"value": None, "error": str(exc)}

            kpi_engine.calculate_all(include_composite=True)
        audit_trail = kpi_engine.get_audit_trail().to_dict(orient="records")

        timeseries = self._compute_timeseries(df, metrics_cfg)
        anomalies = self._detect_anomalies(metrics, baseline_metrics)

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
        )
