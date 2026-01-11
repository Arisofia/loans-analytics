import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.agents.tools import send_slack_notification
from src.pipeline.compliance import (build_compliance_report,
                                     write_compliance_report)
from src.pipeline.config_manager import PipelineConfig
from src.pipeline.data_ingestion import UnifiedIngestion
from src.pipeline.data_transformation import UnifiedTransformation
from src.pipeline.kpi_calculation import UnifiedCalculationV2
from src.pipeline.models import PersistContext
from src.pipeline.output import UnifiedOutput
from src.pipeline.utils import ensure_dir, utc_now, write_json
from src.utils.tracing.setup import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


class UnifiedPipeline:
    """Orchestrate the complete 4-phase data pipeline."""

    ingestor: UnifiedIngestion
    transformer: UnifiedTransformation
    calculator: UnifiedCalculationV2
    output: UnifiedOutput

    def __init__(self, config_path: Optional[Path] = None):
        self.config = PipelineConfig(config_path)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.run_id: Optional[str] = f"pipeline_{timestamp}"
        # Initialize phase components
        self.ingestor = UnifiedIngestion(self.config.config)
        self.transformer = UnifiedTransformation(self.config.config, run_id=self.run_id)
        self.calculator = UnifiedCalculationV2(self.config.config, run_id=self.run_id)
        self.output = UnifiedOutput(self.config.config, run_id=self.run_id)

    def _generate_run_id(self, source_hash: Optional[str]) -> str:
        strategy = self.config.get("run", "id_strategy", default="timestamp")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if strategy == "deterministic" and source_hash:
            return f"run_{source_hash[:12]}"
        if source_hash:
            return f"run_{timestamp}_{source_hash[:6]}"
        return f"run_{timestamp}"

    def _load_previous_metrics(
        self, artifacts_dir: Path, current_run_id: str
    ) -> Optional[Dict[str, Any]]:
        if not artifacts_dir.exists():
            return None
        manifests = sorted(
            artifacts_dir.glob("*/**/*_manifest.json"), key=lambda p: p.stat().st_mtime
        )
        for manifest_path in reversed(manifests):
            if current_run_id in manifest_path.as_posix():
                continue
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                return payload.get("metrics")
            except Exception:
                continue
        return None

    def _handle_alerts(self, ingestion_summary: Dict[str, Any], calculation_result: Any) -> None:
        """Evaluate DQ and KPI statuses to trigger alerts."""
        alerts = []

        # 1. Data Quality Alerts
        dq = ingestion_summary.get("data_quality", {})
        dq_score = dq.get("data_quality_score", 100)
        dq_threshold = 95  # Could be moved to config

        if dq_score < dq_threshold:
            alerts.append(
                f"🔴 *Data Quality Alert*: Score is {dq_score}% (Threshold: {dq_threshold}%)"
            )

        # 2. KPI Threshold Alerts
        for name, metric in calculation_result.metrics.items():
            status = metric.get("status")
            val = metric.get("value")
            disp = metric.get("display_name", name)

            if status == "critical":
                alerts.append(f"🚨 *Critical KPI Alert*: {disp} is {val} (Status: CRITICAL)")
            elif status == "warning":
                alerts.append(f"⚠️ *KPI Warning*: {disp} is {val} (Status: WARNING)")

        if alerts:
            message = f"📢 *Pipeline Alert - Run {self.run_id}*\n\n" + "\n".join(alerts)
            logger.warning("Triggering Slack alerts: %s", alerts)
            send_slack_notification(message, channel="kpi-compliance")

    def _run_ingestion(self, input_file: Path, raw_archive_dir: Path) -> Any:
        with tracer.start_as_current_span("pipeline.ingestion"):
            ingest_cfg = self.config.get("pipeline", "phases", "ingestion", default={}) or {}
            ingest_source = ingest_cfg.get("source", "file")
            cascade_cfg = self.config.get("cascade", default={}) or {}

            if ingest_source == "cascade_http":
                base_url = cascade_cfg.get("base_url", "")
                endpoint = cascade_cfg.get("endpoints", {}).get("loan_tape", "")
                token_env = cascade_cfg.get("auth", {}).get("token_secret")
                token_value = os.getenv(token_env, "") if token_env else ""
                headers = {"Authorization": f"Bearer {token_value}"} if token_value else {}
                url = f"{base_url}{endpoint}"
                return self.ingestor.ingest_http(url, headers=headers)

            if ingest_source == "looker":
                looker_cfg = ingest_cfg.get("looker", {}) or {}
                loans_par_path = looker_cfg.get("loans_par_path")
                loans_fallback_path = looker_cfg.get("loans_path")
                selected_path = None
                if loans_par_path:
                    candidate = Path(loans_par_path)
                    if candidate.exists():
                        selected_path = candidate
                if selected_path is None and loans_fallback_path:
                    selected_path = Path(loans_fallback_path)
                if selected_path is None:
                    selected_path = input_file
                financials_path = looker_cfg.get("financials_path")
                return self.ingestor.ingest_looker(
                    selected_path,
                    financials_path=Path(financials_path) if financials_path else None,
                    archive_dir=raw_archive_dir,
                )

            return self.ingestor.ingest_file(input_file, archive_dir=raw_archive_dir)

    def _run_transformation(self, df: Any, user: str) -> Any:
        with tracer.start_as_current_span("pipeline.transformation") as span:
            if self.run_id:
                self.transformer.run_id = self.run_id
            result = self.transformer.transform(df, user=user)
            span.set_attribute("transformation.row_count", len(result.df))
            span.set_attribute("transformation.masked_columns", len(result.masked_columns))
            return result

    def _run_calculation(self, df: Any, artifacts_dir: Path) -> Any:
        with tracer.start_as_current_span("pipeline.calculation") as span:
            if self.run_id:
                self.calculator.run_id = self.run_id
            baseline_metrics = self._load_previous_metrics(artifacts_dir, self.run_id or "unknown")
            result = self.calculator.calculate(df, baseline_metrics)
            span.set_attribute("calculation.metric_count", len(result.metrics))
            return result

    def _run_compliance(
        self, tx_result: Any, ingestion_result: Any, run_dir: Path, user: str, action: str
    ) -> Path:
        with tracer.start_as_current_span("pipeline.compliance"):
            report = build_compliance_report(
                run_id=self.run_id or "unknown",
                access_log=tx_result.access_log,
                masked_columns=tx_result.masked_columns,
                mask_stage="transformation",
                metadata={
                    "user": user,
                    "action": action,
                    "source_file": ingestion_result.metadata.get("source_file"),
                    "checksum": ingestion_result.metadata.get("checksum"),
                },
            )
            compliance_path = run_dir / f"{self.run_id}_compliance.json"
            write_compliance_report(report, compliance_path)
            return compliance_path

    def _run_output(
        self,
        tx_result: Any,
        calc_result: Any,
        ingestion_result: Any,
        compliance_path: Path,
        user: str,
        action: str,
    ) -> Any:
        with tracer.start_as_current_span("pipeline.output"):
            if self.run_id:
                self.output.run_id = self.run_id
            output_ctx = PersistContext(
                quality_checks=tx_result.quality_checks,
                compliance_report_path=compliance_path,
                timeseries=calc_result.timeseries,
            )
            return self.output.persist(
                tx_result.df,
                calc_result.metrics,
                metadata={
                    "ingestion": ingestion_result.metadata,
                    "lineage": tx_result.lineage,
                    "calculation_audit": calc_result.audit_trail,
                    "anomalies": calc_result.anomalies,
                    "context": {"user": user, "action": action},
                },
                run_ids={
                    "pipeline": self.run_id or "unknown",
                    "ingestion": ingestion_result.run_id,
                    "transformation": tx_result.run_id,
                    "calculation": calc_result.run_id,
                },
                context=output_ctx,
            )

    def execute(
        self, input_file: Path, user: str = "system", action: str = "manual"
    ) -> Dict[str, Any]:
        with tracer.start_as_current_span("pipeline.execute") as span:
            logger.info("Starting unified pipeline execution")
            run_started = utc_now()

            run_cfg = self.config.get("run", default={}) or {}
            artifacts_dir = Path(run_cfg.get("artifacts_dir", "logs/runs"))
            raw_archive_dir = Path(run_cfg.get("raw_archive_dir", "data/archives/cascade"))

            span.set_attribute("pipeline.user", user)
            span.set_attribute("pipeline.action", action)

            try:
                # 1. Ingestion
                ingestion_result = self._run_ingestion(input_file, raw_archive_dir)

                # 2. Run ID Setup
                self.run_id = self._generate_run_id(ingestion_result.source_hash)
                span.set_attribute("pipeline.run_id", self.run_id)
                span.set_attribute("ingestion.row_count", len(ingestion_result.df))
                run_dir = ensure_dir(artifacts_dir / self.run_id)

                # 3. Transformation
                tx_result = self._run_transformation(ingestion_result.df, user)

                # 4. Calculation
                calc_result = self._run_calculation(tx_result.df, artifacts_dir)

                # 5. Alerts
                self._handle_alerts(self.ingestor.get_ingest_summary(), calc_result)

                # 6. Compliance
                compliance_path = self._run_compliance(
                    tx_result, ingestion_result, run_dir, user, action
                )

                # 7. Output
                output_result = self._run_output(
                    tx_result, calc_result, ingestion_result, compliance_path, user, action
                )

                # 8. Summary
                summary = {
                    "status": "success",
                    "run_id": self.run_id,
                    "started_at": run_started,
                    "completed_at": utc_now(),
                    "phases": {
                        "ingestion": {
                            "run_id": ingestion_result.run_id,
                            "rows": len(ingestion_result.df),
                        },
                        "transformation": {
                            "run_id": tx_result.run_id,
                            "rows": len(tx_result.df),
                            "masked_columns": tx_result.masked_columns,
                        },
                        "calculation": {
                            "run_id": calc_result.run_id,
                            "metrics": list(calc_result.metrics.keys()),
                            "anomalies": calc_result.anomalies,
                        },
                        "output": {
                            "manifest": str(output_result.manifest_path),
                            "outputs": output_result.output_paths,
                        },
                    },
                }

                write_json(run_dir / f"{self.run_id}_summary.json", summary)
                return summary

            except Exception as exc:
                span.record_exception(exc)
                logger.error("Pipeline execution failed: %s", str(exc), exc_info=True)
                return {
                    "status": "failed",
                    "run_id": self.run_id,
                    "error": str(exc),
                    "started_at": run_started,
                    "completed_at": utc_now(),
                }

    def run(self, input_file: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        user = context.get("user", "system")
        action = context.get("action", "manual")
        return self.execute(Path(input_file), user=user, action=action)
