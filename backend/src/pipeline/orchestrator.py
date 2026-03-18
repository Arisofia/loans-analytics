"""
UNIFIED PIPELINE ORCHESTRATOR

Coordinates all 4 phases of the data pipeline:
1. Ingestion
2. Transformation
3. Calculation
4. Output

NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/data/run_data_pipeline.py
"""

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend.python.logging_config import get_logger

from .calculation import CalculationPhase
from .config import PipelineConfig, load_business_rules, load_kpi_definitions
from .ingestion import IngestionPhase
from .output import OutputPhase
from .transformation import TransformationPhase

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

OTEL_AVAILABLE = True

logger = get_logger(__name__)


class UnifiedPipeline:
    """
    Unified 4-Phase Pipeline Orchestrator

    Executes the complete data pipeline workflow:
    Input → Ingestion → Transformation → Calculation → Output → Dashboard
    """

    def __init__(self, config_path: Optional[Path] = None, base_log_dir: Optional[Path] = None):
        """
        Initialize the unified pipeline.

        Args:
            config_path: Path to pipeline.yml (optional, defaults to config/pipeline.yml)
            base_log_dir: Base directory for run logs (optional, defaults to logs/runs)
        """
        logger.info("%s", "=" * 80)
        logger.info("UNIFIED PIPELINE ORCHESTRATOR v2.0")
        logger.info("%s", "=" * 80)

        # Load configurations
        self.config = PipelineConfig.load(config_path)
        self.business_rules = load_business_rules()
        self.kpi_definitions = load_kpi_definitions()
        self.base_log_dir = base_log_dir or (Path("logs") / "runs")
        self.enable_tracing = os.getenv("PIPELINE_TRACING_ENABLED", "1") == "1" and OTEL_AVAILABLE
        self._tracer = trace.get_tracer(__name__) if self.enable_tracing else None

        # Initialize phases
        self.ingestion = IngestionPhase(self.config.ingestion)
        self.transformation = TransformationPhase(self.config.transformation, self.business_rules)
        self.calculation = CalculationPhase(self.config.calculation, self.kpi_definitions)
        self.output = OutputPhase(self.config.output)

        logger.info("All pipeline phases initialized successfully")

    def _start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Start an OpenTelemetry span when tracing is enabled."""
        if self._tracer is None:
            return nullcontext(None)
        return self._tracer.start_as_current_span(name, attributes=attributes or {})

    def _execute_phase(
        self,
        *,
        phase_name: str,
        run_id: str,
        executor: Any,
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute one pipeline phase with timing and optional tracing."""
        with self._start_span(
            f"pipeline.{phase_name}",
            {
                "pipeline.run_id": run_id,
                "pipeline.phase": phase_name,
            },
        ) as phase_span:
            started = time.perf_counter()
            try:
                phase_results = executor(**kwargs)
            except Exception as exc:
                if phase_span is not None:
                    phase_span.record_exception(exc)
                    phase_span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise

            duration = round(time.perf_counter() - started, 6)
            phase_results["duration_seconds"] = duration

            if phase_span is not None:
                phase_status = str(phase_results.get("status", "unknown"))
                phase_span.set_attribute("pipeline.phase.status", phase_status)
                phase_span.set_attribute("pipeline.phase.duration_seconds", duration)
                if phase_status == "success":
                    phase_span.set_status(Status(StatusCode.OK))
                else:
                    phase_span.set_status(
                        Status(StatusCode.ERROR, str(phase_results.get("error", "phase_failed")))
                    )

            return phase_results

    def execute(self, input_path: Optional[Path] = None, mode: str = "full") -> Dict[str, Any]:
        """
        Execute the complete pipeline.

        Args:
            input_path: Path to input CSV file (optional)
            mode: Execution mode - 'full', 'validate', 'dry-run'

        Returns:
            Pipeline execution results
        """
        # Calculate deterministic run_id for idempotency.
        # run_signature = hash(data_hash + config_hash + code_version + mode)
        # so that any change in data, config, code version, or mode produces a new run.
        mode_token = mode.replace("-", "_")
        if input_path and input_path.exists():
            data_hash = self._calculate_input_hash(input_path)
        else:
            data_hash = "nofile"

        config_hash = self._calculate_config_hash()
        code_version = self._get_code_version()
        run_signature = self._calculate_run_signature(data_hash, config_hash, code_version, mode_token)
        base_run_id = f"{datetime.now().strftime('%Y%m%d')}_{run_signature[:8]}"
        run_id = base_run_id if mode == "full" else f"{base_run_id}_{mode_token}"

        logger.info("Starting pipeline execution (run_id: %s, mode: %s)", run_id, mode)

        # Create run directory
        run_dir = self.base_log_dir / run_id

        # Check for existing run (idempotency)
        if run_dir.exists():
            manifest_path = run_dir / "pipeline_results.json"
            if manifest_path.exists():
                logger.info(
                    "Run %s already exists, loading existing results (idempotent)",
                    run_id,
                )

                with open(manifest_path, "r") as f:
                    return json.load(f)

        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Run directory: %s", run_dir)

        results: Dict[str, Any] = {
            "run_id": run_id,
            "mode": mode,
            "start_time": datetime.now().isoformat(),
            "phases": {},
            "phase_metrics": {},
        }

        with self._start_span(
            "pipeline.execute",
            {
                "pipeline.run_id": run_id,
                "pipeline.mode": mode,
            },
        ) as pipeline_span:
            try:
                # PHASE 1: INGESTION
                separator = "=" * 80
                logger.info("\n%s", separator)
                logger.info("PHASE 1: INGESTION")
                logger.info("%s", separator)
                phase1_results = self._execute_phase(
                    phase_name="ingestion",
                    run_id=run_id,
                    executor=self.ingestion.execute,
                    kwargs={"input_path": input_path, "run_dir": run_dir},
                )
                results["phases"]["ingestion"] = phase1_results
                results["phase_metrics"]["ingestion"] = {
                    "status": phase1_results.get("status"),
                    "duration_seconds": phase1_results.get("duration_seconds", 0.0),
                }

                if phase1_results["status"] != "success":
                    error_msg = f"Phase 1 (Ingestion) failed: {phase1_results.get('error')}"
                    raise RuntimeError(error_msg)

                if mode == "dry-run":
                    logger.info("Dry-run mode: stopping after ingestion")
                    final_results = self._finalize_results(results, run_dir)
                    if pipeline_span is not None:
                        pipeline_span.set_attribute("pipeline.status", final_results["status"])
                        pipeline_span.set_attribute(
                            "pipeline.duration_seconds", final_results["duration_seconds"]
                        )
                        pipeline_span.set_status(Status(StatusCode.OK))
                    return final_results

                # PHASE 2: TRANSFORMATION
                logger.info("\n%s", separator)
                logger.info("PHASE 2: TRANSFORMATION")
                logger.info("%s", separator)
                raw_data_path = (
                    Path(phase1_results["output_path"])
                    if phase1_results.get("output_path")
                    else None
                )
                phase2_results = self._execute_phase(
                    phase_name="transformation",
                    run_id=run_id,
                    executor=self.transformation.execute,
                    kwargs={"raw_data_path": raw_data_path, "run_dir": run_dir},
                )
                results["phases"]["transformation"] = phase2_results
                results["phase_metrics"]["transformation"] = {
                    "status": phase2_results.get("status"),
                    "duration_seconds": phase2_results.get("duration_seconds", 0.0),
                }

                if phase2_results["status"] != "success":
                    error_msg = f"Phase 2 (Transformation) failed: {phase2_results.get('error')}"
                    raise RuntimeError(error_msg)

                if mode == "validate":
                    logger.info("Validate mode: stopping after transformation")
                    final_results = self._finalize_results(results, run_dir)
                    if pipeline_span is not None:
                        pipeline_span.set_attribute("pipeline.status", final_results["status"])
                        pipeline_span.set_attribute(
                            "pipeline.duration_seconds", final_results["duration_seconds"]
                        )
                        pipeline_span.set_status(Status(StatusCode.OK))
                    return final_results

                # PHASE 3: CALCULATION
                logger.info("\n%s", separator)
                logger.info("PHASE 3: CALCULATION")
                logger.info("%s", separator)
                clean_data_path = (
                    Path(phase2_results["output_path"])
                    if phase2_results.get("output_path")
                    else None
                )
                phase3_results = self._execute_phase(
                    phase_name="calculation",
                    run_id=run_id,
                    executor=self.calculation.execute,
                    kwargs={"clean_data_path": clean_data_path, "run_dir": run_dir},
                )
                results["phases"]["calculation"] = phase3_results
                results["phase_metrics"]["calculation"] = {
                    "status": phase3_results.get("status"),
                    "duration_seconds": phase3_results.get("duration_seconds", 0.0),
                }

                if phase3_results["status"] != "success":
                    error_msg = f"Phase 3 (Calculation) failed: {phase3_results.get('error')}"
                    raise RuntimeError(error_msg)

                # PHASE 4: OUTPUT
                logger.info("\n%s", separator)
                logger.info("PHASE 4: OUTPUT")
                logger.info("%s", separator)
                phase4_results = self._execute_phase(
                    phase_name="output",
                    run_id=run_id,
                    executor=self.output.execute,
                    kwargs={
                        "kpi_results": phase3_results.get("kpis", {}),
                        "run_dir": run_dir,
                        "kpi_engine": phase3_results.get("kpi_engine"),
                        "segment_kpis": phase3_results.get("segment_kpis"),
                        "time_series": phase3_results.get("time_series"),
                        "anomalies": phase3_results.get("anomalies"),
                        "nsm_recurrent_tpv": phase3_results.get("nsm_recurrent_tpv"),
                        "clustering_metrics": phase3_results.get("clustering_metrics"),
                        "transformation_metrics": phase2_results.get("transformation_metrics"),
                    },
                )
                results["phases"]["output"] = phase4_results
                results["phase_metrics"]["output"] = {
                    "status": phase4_results.get("status"),
                    "duration_seconds": phase4_results.get("duration_seconds", 0.0),
                }

                if phase4_results["status"] != "success":
                    error_msg = f"Phase 4 (Output) failed: {phase4_results.get('error')}"
                    raise RuntimeError(error_msg)

                final_results = self._finalize_results(results, run_dir)
                if pipeline_span is not None:
                    pipeline_span.set_attribute("pipeline.status", final_results["status"])
                    pipeline_span.set_attribute(
                        "pipeline.duration_seconds", final_results["duration_seconds"]
                    )
                    pipeline_span.set_status(Status(StatusCode.OK))
                return final_results

            except Exception as e:
                logger.error("Pipeline execution failed: %s", e)
                logger.error("%s", traceback.format_exc())

                results["status"] = "failed"
                results["error"] = str(e)
                results["traceback"] = traceback.format_exc()

                final_results = self._finalize_results(results, run_dir)
                if pipeline_span is not None:
                    pipeline_span.record_exception(e)
                    pipeline_span.set_attribute("pipeline.status", final_results["status"])
                    pipeline_span.set_attribute(
                        "pipeline.duration_seconds", final_results["duration_seconds"]
                    )
                    pipeline_span.set_status(Status(StatusCode.ERROR, str(e)))
                return final_results

    def _finalize_results(self, results: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
        """Finalize pipeline results."""
        results["end_time"] = datetime.now().isoformat()

        # Calculate duration
        start = datetime.fromisoformat(results["start_time"])
        end = datetime.fromisoformat(results["end_time"])
        duration = (end - start).total_seconds()
        results["duration_seconds"] = duration

        # Determine overall status
        if "status" not in results:
            all_success = all(
                phase.get("status") == "success" for phase in results["phases"].values()
            )
            results["status"] = "success" if all_success else "partial"

        # Save results manifest
        manifest_path = run_dir / "pipeline_results.json"
        with open(manifest_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        separator = "=" * 80
        logger.info("\n%s", separator)
        logger.info("PIPELINE EXECUTION COMPLETE")
        logger.info("Status: %s", results["status"].upper())
        logger.info("Duration: %.2f seconds", duration)
        logger.info("Results: %s", manifest_path)
        logger.info("%s", separator)

        return results

    def _calculate_input_hash(self, file_path: Path) -> str:
        """
        Calculate deterministic hash of input file for idempotency.

        Args:
            file_path: Path to input file

        Returns:
            SHA256 hash (first 16 chars)
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except Exception as e:
            logger.warning("Failed to hash input file: %s, using timestamp", e)
            return datetime.now().strftime("%H%M%S")

    def _calculate_config_hash(self) -> str:
        """Calculate deterministic hash of the pipeline configuration.

        Ensures that a config change (e.g. new business rules, KPI thresholds)
        forces a fresh run even when the input data has not changed.
        """
        try:
            config_str = json.dumps(
                {
                    "transformation": self.config.transformation,
                    "calculation": self.config.calculation,
                    "output": self.config.output,
                },
                sort_keys=True,
                default=str,
            )
            return hashlib.sha256(config_str.encode()).hexdigest()[:16]
        except Exception as e:
            logger.warning("Failed to hash pipeline config: %s, using empty string", e)
            return "00000000"

    @staticmethod
    def _get_code_version() -> str:
        """Return the current pipeline code version."""
        try:
            from backend.src.pipeline import __version__  # type: ignore[attr-defined]
            return __version__
        except Exception:
            return "unknown"

    @staticmethod
    def _calculate_run_signature(
        data_hash: str, config_hash: str, code_version: str, mode: str
    ) -> str:
        """Compose a cryptographic run signature from all deterministic inputs.

        ``run_signature = SHA256(data_hash + config_hash + code_version + mode)``

        This guarantees idempotency: two pipeline invocations with identical
        data, config, code version, and mode always produce the same run_id
        and therefore reuse cached results.  Any single change produces a new id.
        """
        composite = "|".join([data_hash, config_hash, code_version, mode])
        return hashlib.sha256(composite.encode()).hexdigest()[:16]


def main() -> int:
    """
    CLI entry point for the unified pipeline.

    Supports multiple execution modes:
    - full: All 4 phases (Ingestion → Transformation → Calculation → Output)
    - validate: Stop after transformation (for schema validation)
    - dry-run: Stop after ingestion (for data source testing)

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    parser = argparse.ArgumentParser(
        description=(
            "Unified 4-Phase Data Pipeline " "(Ingestion → Transformation → Calculation → Output)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Run full pipeline with a specific CSV input file
  python scripts/data/run_data_pipeline.py --input /path/to/your/data.csv

  # Live mode (alias for full - all 4 phases)
  python scripts/data/run_data_pipeline.py --mode live --input data/raw/abaco_real_data_20260202.csv

  # Validation mode (stop after transformation)
  python scripts/data/run_data_pipeline.py --mode validate

  # Dry-run mode (stop after ingestion)
  python scripts/data/run_data_pipeline.py --mode dry-run

  # Custom config file
  python scripts/data/run_data_pipeline.py --config config/custom_pipeline.yml
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input CSV file (optional, uses config default)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/pipeline.yml",
        help="Path to pipeline.yml config (default: config/pipeline.yml)",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "live", "validate", "dry-run"],
        default="full",
        help=(
            "Execution mode: full/live (all phases), "
            "validate (stop after transformation), "
            "dry-run (stop after ingestion)"
        ),
    )

    args = parser.parse_args()

    try:
        # Initialize pipeline
        config_path = Path(args.config) if args.config else None
        pipeline = UnifiedPipeline(config_path=config_path)

        # Execute pipeline ('live' is an alias for 'full')
        input_path = Path(args.input) if args.input else None
        mode = "full" if args.mode == "live" else args.mode
        results = pipeline.execute(input_path=input_path, mode=mode)

        # Check status
        if results.get("status") == "success":
            logger.info("✓ Pipeline completed successfully")
            return 0

        error_msg = results.get("error", "Unknown error")
        logger.error("✗ Pipeline failed: %s", error_msg)
        return 1

    except Exception as e:
        logger.error("Fatal error: %s", e)
        logger.error("%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
