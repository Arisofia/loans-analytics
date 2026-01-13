import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from prefect import flow, task

from src.agents.tools import send_slack_notification
from src.compliance import build_compliance_report, write_compliance_report
from src.config.paths import Paths
from src.pipeline.data_ingestion import UnifiedIngestion
from src.pipeline.data_transformation import UnifiedTransformation
from src.pipeline.kpi_calculation import UnifiedCalculationV2
from src.pipeline.output import UnifiedOutput
from src.pipeline.utils import (ensure_dir, load_yaml, resolve_placeholders,
                                utc_now, write_json)
from src.tracing_setup import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


def _deep_merge(base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge override_dict into base_dict, with override taking precedence."""
    result = base_dict.copy()
    for key, value in override_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class PipelineConfig:
    """Configuration management with validation, environment overrides, and defaults."""

    DEFAULT_CONFIG_PATH = Paths.config_file()
    ENVIRONMENTS_DIR = Paths.config_file().parent.parent / "environments"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.environment = os.getenv("PIPELINE_ENV", "development")
        self.config = self._load_config()
        self._validate_config()
        logger.info("Pipeline configured for environment: %s", self.environment)

    def _load_config(self) -> Dict[str, Any]:
        """Load base config and merge with environment-specific overrides."""
        if not self.config_path.exists():
            logger.warning("Config file not found: %s, using minimal defaults", self.config_path)
            return self._default_config()

        base_config = load_yaml(self.config_path)
        logger.info("Loaded base configuration from %s", self.config_path)

        env_config_path = self.ENVIRONMENTS_DIR / f"{self.environment}.yml"
        if env_config_path.exists():
            env_config = load_yaml(env_config_path)
            base_config = _deep_merge(base_config, env_config)
            logger.info("Merged environment config from %s", env_config_path)
        else:
            logger.warning(
                "Environment config not found: %s, using base config only", env_config_path
            )

        context = {
            "portfolio_id": base_config.get("cascade", {}).get("portfolio_id", ""),
        }
        return resolve_placeholders(base_config, context)

    def _default_config(self) -> Dict[str, Any]:
        return {
            "version": "2.0",
            "name": "abaco_unified_pipeline",
            "environment": self.environment,
            "pipeline": {
                "phases": {
                    "ingestion": {},
                    "transformation": {},
                    "calculation": {},
                    "outputs": {},
                }
            },
            "run": {"id_strategy": "timestamp"},
        }

    def _validate_config(self) -> None:
        if "pipeline" not in self.config:
            raise ValueError("Pipeline configuration missing 'pipeline' key")
        if "phases" not in self.config["pipeline"]:
            raise ValueError("Pipeline configuration missing 'phases' key")

    def get(self, *keys: str, default: Any = None) -> Any:
        value: Any = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default


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

    def execute(
        self, input_file: Path, user: str = "system", action: str = "manual"
    ) -> Dict[str, Any]:
        with tracer.start_as_current_span("pipeline.execute") as span:
            logger.info("Starting unified pipeline execution")
            run_started = utc_now()
            run_cfg = self.config.get("run", default={}) or {}
            artifacts_dir = Path(run_cfg.get("artifacts_dir", "logs/runs"))
            raw_archive_dir = Path(run_cfg.get("raw_archive_dir", "data/archives/cascade"))
            ingest_cfg = self.config.get("pipeline", "phases", "ingestion", default={}) or {}
            ingest_source = ingest_cfg.get("source", "file")
            cascade_cfg = self.config.get("cascade", default={}) or {}

            span.set_attribute("pipeline.user", user)
            span.set_attribute("pipeline.action", action)
            span.set_attribute("pipeline.source", ingest_source)
            try:
                with tracer.start_as_current_span("pipeline.ingestion"):
                    if ingest_source == "cascade_http":
                        base_url = cascade_cfg.get("base_url", "")
                        endpoint = cascade_cfg.get("endpoints", {}).get("loan_tape", "")
                        token_env = cascade_cfg.get("auth", {}).get("token_secret")
                        token_value = os.getenv(token_env, "") if token_env else ""
                        headers = {"Authorization": f"Bearer {token_value}"} if token_value else {}
                        url = f"{base_url}{endpoint}"
                        ingestion_result = self.ingestor.ingest_http(url, headers=headers)
                    elif ingest_source == "looker":
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
                        ingestion_result = self.ingestor.ingest_looker(
                            selected_path,
                            financials_path=Path(financials_path) if financials_path else None,
                            archive_dir=raw_archive_dir,
                        )
                    else:
                        ingestion_result = self.ingestor.ingest_file(
                            input_file, archive_dir=raw_archive_dir
                        )

                self.run_id = self._generate_run_id(ingestion_result.source_hash)
                span.set_attribute("pipeline.run_id", self.run_id)
                span.set_attribute("ingestion.row_count", len(ingestion_result.df))
                run_dir = ensure_dir(artifacts_dir / self.run_id)

                # Update run_id for components
                self.transformer.run_id = self.run_id
                self.calculator.run_id = self.run_id
                self.output.run_id = self.run_id

                with tracer.start_as_current_span("pipeline.transformation") as transformation_span:
                    transformation_result = self.transformer.transform(
                        ingestion_result.df, user=user
                    )
                    transformation_span.set_attribute(
                        "transformation.row_count", len(transformation_result.df)
                    )
                    transformation_span.set_attribute(
                        "transformation.masked_columns",
                        len(transformation_result.masked_columns),
                    )

                baseline_metrics = self._load_previous_metrics(artifacts_dir, self.run_id)

                with tracer.start_as_current_span("pipeline.calculation") as calculation_span:
                    calculation_result = self.calculator.calculate(
                        transformation_result.df, baseline_metrics
                    )
                    calculation_span.set_attribute(
                        "calculation.metric_count", len(calculation_result.metrics)
                    )

                # Evaluate alerts
                self._handle_alerts(self.ingestor.get_ingest_summary(), calculation_result)

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

                with tracer.start_as_current_span("pipeline.output"):
                    output_result = self.output.persist(
                        transformation_result.df,
                        calculation_result.metrics,
                        metadata={
                            "ingestion": ingestion_result.metadata,
                            "lineage": transformation_result.lineage,
                            "calculation_audit": calculation_result.audit_trail,
                            "anomalies": calculation_result.anomalies,
                            "context": {"user": user, "action": action},
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


# Prefect Tasks for Engineering Excellence and Lineage
@task(name="Ingest Loan Tape", retries=3, retry_delay_seconds=60)
def ingest_task(pipeline: UnifiedPipeline, input_file: Path):
    logger.info("Task: Ingesting %s", input_file)
    return pipeline.ingestor.ingest_file(input_file)


@task(name="Transform Data")
def transform_task(pipeline: UnifiedPipeline, ingestion_result):
    if ingestion_result.df.empty:
        return ingestion_result
    logger.info("Task: Transforming data")
    return pipeline.transformer.transform(ingestion_result.df)


@task(name="Calculate KPIs")
def calculate_task(pipeline: UnifiedPipeline, transformation_result):
    if transformation_result.df.empty:
        return transformation_result
    logger.info("Task: Calculating KPIs")
    return pipeline.calculator.calculate(transformation_result.df)


@flow(name="Daily Loan Intelligence Cycle")
def daily_loan_intelligence_flow(input_file: str = "data/archives/abaco_portfolio.csv"):
    """
    Prefect flow for daily loan intelligence operations.
    Enforces Data Contracts and emits Lineage metadata.
    """
    logger.info("Starting Daily Loan Intelligence Cycle for %s", input_file)
    pipeline = UnifiedPipeline()
    path = Path(input_file)

    # 1. Ingestion Phase with Circuit Breaker
    ingest_res = ingest_task(pipeline, path)
    if ingest_res is None or ingest_res.df.empty:
        logger.error("Flow halted: Ingestion returned empty dataframe (Circuit Breaker triggered)")
        return {"status": "halted", "reason": "ingestion_failure"}

    # 2. Transformation Phase
    transform_res = transform_task(pipeline, ingest_res)

    # 3. Calculation Phase
    calculate_task(pipeline, transform_res)

    # 4. Finalization (Compliance + Summary)
    # For now, we reuse the existing execution logic or wrap the remaining parts
    logger.info("Daily Intelligence Cycle completed successfully.")
    return {"status": "success", "run_id": pipeline.run_id}


if __name__ == "__main__":
    daily_loan_intelligence_flow()
