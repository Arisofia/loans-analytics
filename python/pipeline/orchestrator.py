import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from python.compliance import build_compliance_report, write_compliance_report
from python.pipeline.calculation import UnifiedCalculationV2
from python.pipeline.ingestion import UnifiedIngestion
from python.pipeline.output import UnifiedOutput
from python.pipeline.transformation import UnifiedTransformation
from python.pipeline.utils import ensure_dir, load_yaml, resolve_placeholders, utc_now, write_json

logger = logging.getLogger(__name__)


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

    DEFAULT_CONFIG_PATH = Path("config/pipeline.yml")
    ENVIRONMENTS_DIR = Path("config/environments")

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

    def __init__(self, config_path: Optional[Path] = None):
        self.config = PipelineConfig(config_path)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.run_id: Optional[str] = f"pipeline_{timestamp}"

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

    def execute(
        self, input_file: Path, user: str = "system", action: str = "manual"
    ) -> Dict[str, Any]:
        logger.info("Starting unified pipeline execution")
        run_started = utc_now()
        run_cfg = self.config.get("run", default={}) or {}
        artifacts_dir = Path(run_cfg.get("artifacts_dir", "logs/runs"))
        raw_archive_dir = Path(run_cfg.get("raw_archive_dir", "data/raw/cascade"))
        ingest_cfg = self.config.get("pipeline", "phases", "ingestion", default={}) or {}
        ingest_source = ingest_cfg.get("source", "file")
        cascade_cfg = self.config.get("cascade", default={}) or {}

        try:
            ingestion = UnifiedIngestion(self.config.config)
            if ingest_source == "cascade_http":
                base_url = cascade_cfg.get("base_url", "")
                endpoint = cascade_cfg.get("endpoints", {}).get("loan_tape", "")
                token_env = cascade_cfg.get("auth", {}).get("token_secret")
                token_value = os.getenv(token_env, "") if token_env else ""
                headers = {"Authorization": f"Bearer {token_value}"} if token_value else {}
                url = f"{base_url}{endpoint}"
                ingestion_result = ingestion.ingest_http(url, headers=headers)
            else:
                ingestion_result = ingestion.ingest_file(input_file, archive_dir=raw_archive_dir)

            self.run_id = self._generate_run_id(ingestion_result.source_hash)
            run_dir = ensure_dir(artifacts_dir / self.run_id)

            transformation = UnifiedTransformation(self.config.config, run_id=self.run_id)
            transformation_result = transformation.transform(ingestion_result.df, user=user)

            baseline_metrics = self._load_previous_metrics(artifacts_dir, self.run_id)
            calculation = UnifiedCalculationV2(self.config.config, run_id=self.run_id)
            calculation_result = calculation.calculate(transformation_result.df, baseline_metrics)

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

            output = UnifiedOutput(self.config.config, run_id=self.run_id)
            output_result = output.persist(
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
