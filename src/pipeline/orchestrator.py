import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from prefect import flow, task

from src.compliance import build_compliance_report, write_compliance_report
from src.pipeline.config import PipelineConfig
from src.pipeline.data_ingestion import IngestionResult, UnifiedIngestion
from src.pipeline.data_transformation import UnifiedTransformation
from src.pipeline.kpi_calculation import UnifiedCalculationV2
from src.pipeline.output import UnifiedOutput
from src.pipeline.utils import ensure_dir, utc_now, write_json
from src.tracing_setup import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


class UnifiedPipeline:
    """Orchestrate the complete 4-phase data pipeline."""

    ingestor: UnifiedIngestion
    transformer: UnifiedTransformation
    calculator: UnifiedCalculationV2
    output: UnifiedOutput

    def __init__(
        self, config_path: Optional[Path] = None, config_overrides: Optional[Dict[str, Any]] = None
    ):
        self.config = PipelineConfig(config_path, overrides=config_overrides)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.run_id: str = f"pipeline_{timestamp}"

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
        # Sort manifests by modification time descending (newest first)
        manifests = sorted(
            artifacts_dir.glob("*/**/*_manifest.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for manifest_path in manifests:
            # Skip the current run's manifest to avoid self-reference
            if current_run_id in manifest_path.as_posix():
                continue
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                return payload.get("metrics")
            except (json.JSONDecodeError, OSError) as e:
                # Handle expected file/parsing errors gracefully by logging a warning
                # and trying the next available manifest.
                logger.warning(f"Skipping corrupt or missing manifest {manifest_path}: {e}")
                continue
            except Exception as e:
                # Log unexpected errors with a traceback but don't crash the pipeline
                logger.error(f"Unexpected error reading {manifest_path}: {e}", exc_info=True)
                continue
        return None

    def _handle_alerts(self, ingestion_summary: Dict[str, Any], calculation_result: Any) -> None:
        """Evaluate DQ and KPI statuses to trigger alerts."""
        alerts = []

        # 1. Data Quality Alerts
        dq = ingestion_summary.get("data_quality", {})
        dq_score = dq.get("data_quality_score", 100)
        dq_threshold = self.config.get(
            "pipeline", "phases", "ingestion", "validation", "threshold", default=95
        )

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
            _ = f"📢 *Pipeline Alert - Run {self.run_id}*\n\n" + "\n".join(alerts)
            logger.warning("Pipeline Alerts: %s", alerts)

    def execute(
        self, input_file: Path, user: str = "system", action: str = "manual"
    ) -> Dict[str, Any]:
        with tracer.start_as_current_span("pipeline.execute") as span:
            logger.info("Starting unified pipeline execution")
            run_started = utc_now()

            run_cfg = self.config.get("run", default={}) or {}
            artifacts_dir = Path(run_cfg.get("artifacts_dir", "logs/runs"))
            raw_archive_dir = Path(run_cfg.get("raw_archive_dir", "data/archives/raw"))

            span.set_attribute("pipeline.user", user)
            span.set_attribute("pipeline.action", action)

            try:
                # 1. Ingestion
                ingestion_result = self._ingestion_phase(input_file, raw_archive_dir)

                # 2. Update Run ID and Components
                self.run_id = self._generate_run_id(ingestion_result.source_hash)
                span.set_attribute("pipeline.run_id", self.run_id)
                self._update_component_run_ids()

                run_dir = ensure_dir(artifacts_dir / self.run_id)

                # 3. Transformation
                transformation_result = self._transformation_phase(ingestion_result, user)

                # 4. Calculation
                baseline_metrics = self._load_previous_metrics(artifacts_dir, self.run_id)
                calculation_result = self._calculation_phase(
                    transformation_result, baseline_metrics
                )

                # 5. Alerts
                self._handle_alerts(self.ingestor.get_ingest_summary(), calculation_result)

                # 6. Compliance
                compliance_path = self._compliance_phase(
                    transformation_result, ingestion_result, run_dir, user, action
                )

                # 7. Output
                output_result = self._output_phase(
                    transformation_result,
                    calculation_result,
                    ingestion_result,
                    compliance_path,
                    user,
                    action,
                )

                # 8. Summary
                summary = self._summarize(
                    run_started,
                    ingestion_result,
                    transformation_result,
                    calculation_result,
                    output_result,
                )

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

    def _update_component_run_ids(self) -> None:
        """Update run_id for all pipeline components."""
        self.transformer.run_id = self.run_id
        self.calculator.run_id = self.run_id
        self.output.run_id = self.run_id

    def _ingestion_phase(self, input_file: Path, archive_dir: Path) -> IngestionResult:
        with tracer.start_as_current_span("pipeline.ingestion") as span:
            result = self.ingestor.ingest(input_file, archive_dir=archive_dir)
            span.set_attribute("ingestion.row_count", len(result.df))
            return result

    def _transformation_phase(self, ingestion_result: IngestionResult, user: str) -> Any:
        with tracer.start_as_current_span("pipeline.transformation") as span:
            result = self.transformer.transform(ingestion_result.df, user=user)
            span.set_attribute("transformation.row_count", len(result.df))
            span.set_attribute("transformation.masked_columns", len(result.masked_columns))
            return result

    def _calculation_phase(
        self, transformation_result: Any, baseline_metrics: Optional[Dict[str, Any]]
    ) -> Any:
        with tracer.start_as_current_span("pipeline.calculation") as span:
            result = self.calculator.calculate(transformation_result.df, baseline_metrics)
            span.set_attribute("calculation.metric_count", len(result.metrics))
            return result

    def _compliance_phase(
        self,
        transformation_result: Any,
        ingestion_result: IngestionResult,
        run_dir: Path,
        user: str,
        action: str,
    ) -> Path:
        with tracer.start_as_current_span("pipeline.compliance"):
            compliance_report = build_compliance_report(
                run_id=self.run_id,
                access_log=transformation_result.access_log,
                masked_columns=transformation_result.masked_columns,
                mask_stage="transformation",
                metadata={
                    "user": user,
                    "action": action,
                    "source_file": ingestion_result.metadata.get("source_file"),
                    "checksum": ingestion_result.metadata.get("checksum"),
                },
            )
            compliance_path = run_dir / f"{self.run_id}_compliance.json"
            write_compliance_report(compliance_report, compliance_path)
            return compliance_path

    def _output_phase(
        self,
        transformation_result: Any,
        calculation_result: Any,
        ingestion_result: IngestionResult,
        compliance_path: Path,
        user: str,
        action: str,
    ) -> Any:
        with tracer.start_as_current_span("pipeline.output"):
            return self.output.persist(
                transformation_result.df,
                calculation_result.metrics,
                metadata={
                    "ingestion": ingestion_result.metadata,
                    "lineage": transformation_result.lineage,
                    "calculation_audit": calculation_result.audit_trail,
                    "anomalies": calculation_result.anomalies,
                    "context": {"user": user, "action": action},
                    "extended_kpis": calculation_result.extended_kpis,
                },
                run_ids={
                    "pipeline": self.run_id,
                    "ingestion": ingestion_result.run_id,
                    "transformation": transformation_result.run_id,
                    "calculation": calculation_result.run_id,
                },
                quality_checks=transformation_result.quality_checks,
                compliance_report_path=compliance_path,
                timeseries=calculation_result.timeseries,
            )

    def _summarize(
        self,
        run_started: str,
        ingestion_result: IngestionResult,
        transformation_result: Any,
        calculation_result: Any,
        output_result: Any,
    ) -> Dict[str, Any]:
        return {
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
                    "run_id": transformation_result.run_id,
                    "rows": len(transformation_result.df),
                    "masked_columns": transformation_result.masked_columns,
                },
                "calculation": {
                    "run_id": calculation_result.run_id,
                    "metrics": list(calculation_result.metrics.keys()),
                    "anomalies": calculation_result.anomalies,
                },
                "output": {
                    "manifest": str(output_result.manifest_path),
                    "outputs": output_result.output_paths,
                },
            },
        }

    def run(self, input_file: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        user = context.get("user", "system")
        action = context.get("action", "manual")
        return self.execute(Path(input_file), user=user, action=action)


# Prefect Tasks for Engineering Excellence and Lineage
@task(name="Ingest Loan Tape", retries=3, retry_delay_seconds=60)
def ingest_task(pipeline: UnifiedPipeline, input_file: Path) -> IngestionResult:
    run_cfg = pipeline.config.get("run", default={}) or {}
    archive_dir = Path(run_cfg.get("raw_archive_dir", "data/archives/raw"))
    return pipeline._ingestion_phase(input_file, archive_dir)


@task(name="Transform Data")
def transform_task(pipeline: UnifiedPipeline, ingestion_result: IngestionResult, user: str) -> Any:
    return pipeline._transformation_phase(ingestion_result, user)


@task(name="Calculate KPIs")
def calculate_task(
    pipeline: UnifiedPipeline, transformation_result: Any, artifacts_dir: Path
) -> Any:
    baseline = pipeline._load_previous_metrics(artifacts_dir, pipeline.run_id or "")
    return pipeline._calculation_phase(transformation_result, baseline)


@task(name="Persist Results")
def output_task(
    pipeline: UnifiedPipeline,
    transformation_result: Any,
    calculation_result: Any,
    ingestion_result: IngestionResult,
    run_dir: Path,
    user: str,
    action: str,
) -> Dict[str, Any]:
    # Compliance first
    compliance_path = pipeline._compliance_phase(
        transformation_result, ingestion_result, run_dir, user, action
    )
    # Then output
    pipeline._output_phase(
        transformation_result, calculation_result, ingestion_result, compliance_path, user, action
    )
    return pipeline.ingestor.get_ingest_summary()


@flow(name="Abaco Data Pipeline V2")
def abaco_pipeline_flow(input_file: str, user: str = "system"):
    pipeline = UnifiedPipeline()
    input_path = Path(input_file)

    run_cfg = pipeline.config.get("run", default={}) or {}
    artifacts_dir = Path(run_cfg.get("artifacts_dir", "logs/runs"))

    # Execute tasks
    ingest_res = ingest_task(pipeline, input_path)

    # Update pipeline run_id after ingestion (if deterministic)
    pipeline.run_id = pipeline._generate_run_id(ingest_res.source_hash)
    pipeline._update_component_run_ids()
    run_dir = ensure_dir(artifacts_dir / pipeline.run_id)

    trans_res = transform_task(pipeline, ingest_res, user)
    calc_res = calculate_task(pipeline, trans_res, artifacts_dir)

    # Alerting
    pipeline._handle_alerts(pipeline.ingestor.get_ingest_summary(), calc_res)

    # Finalize
    output_task(pipeline, trans_res, calc_res, ingest_res, run_dir, user, "automated")

    return {"status": "success", "run_id": pipeline.run_id}
