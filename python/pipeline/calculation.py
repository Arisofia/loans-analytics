import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from python.kpi_engine import KPIEngine

logger = logging.getLogger(__name__)

class CalculationResult:
    """Container for KPI calculation outputs and audit trail."""
    def __init__(self, metrics: Dict[str, Any], audit_trail: List[Dict[str, Any]], run_id: str):
        self.metrics = metrics
        self.audit_trail = audit_trail
        self.run_id = run_id
        self.timestamp = datetime.now(timezone.utc).isoformat()

class UnifiedCalculation:
    """Phase 3: KPI Computation and Enrichment with formula traceability."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("pipeline", {}).get("phases", {}).get("calculation", {})
        self.run_id = f"calc_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        }
        self.audit_log.append(entry)
        logger.info(f"[Calculation:{event}] {status} | {details}")

    def calculate(self, df: pd.DataFrame) -> CalculationResult:
        """Execute the calculation phase using configuration-driven metrics."""
        self._log_event("start", "initiated", rows=len(df))
        
        if df.empty:
            self._log_event("execution", "skipped", reason="Empty DataFrame")
            return CalculationResult({}, [], self.run_id)

        try:
            kpi_engine = KPIEngine(df, actor="unified_pipeline", action="batch_calc")
            
            # Map of config name -> engine method
            method_map = {
                "PAR30": kpi_engine.calculate_par_30,
                "PAR90": kpi_engine.calculate_par_90,
                "CollectionRate": kpi_engine.calculate_collection_rate,
            }

            calculated_metrics = {}
            
            # Phase 3.1: Config-Driven KPI Calculation
            metrics_to_run = self.config.get("metrics", [])
            for metric_cfg in metrics_to_run:
                name = metric_cfg["name"]
                if name in method_map:
                    val, ctx = method_map[name]()
                    calculated_metrics[name] = {
                        "value": val,
                        "formula": metric_cfg.get("formula"),
                        "source": metric_cfg.get("source"),
                        **ctx
                    }
                    self._log_event("metric_computed", "success", metric=name, value=val)
            
            # Phase 3.2: Enrichment (Health Score)
            if "PAR30" in calculated_metrics and "CollectionRate" in calculated_metrics:
                h_val, h_ctx = kpi_engine.calculate_portfolio_health(
                    calculated_metrics["PAR30"]["value"],
                    calculated_metrics["CollectionRate"]["value"]
                )
                calculated_metrics["HealthScore"] = {
                    "value": h_val,
                    "formula": "calculate_portfolio_health",
                    **h_ctx
                }
                self._log_event("metric_computed", "success", metric="HealthScore", value=h_val)

            audit_trail = kpi_engine.get_audit_trail().to_dict(orient="records")
            
            self._log_event("complete", "success", metric_count=len(calculated_metrics))
            
            return CalculationResult(calculated_metrics, audit_trail, self.run_id)

        except Exception as e:
            self._log_event("fatal_error", "failed", error=str(e))
            raise
