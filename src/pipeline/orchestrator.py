"""
UNIFIED PIPELINE ORCHESTRATOR

Coordinates all 4 phases of the data pipeline:
1. Ingestion
2. Transformation
3. Calculation
4. Output

Entry point: scripts/run_data_pipeline.py
"""

import hashlib
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from python.logging_config import get_logger

from .calculation import CalculationPhase
from .config import PipelineConfig, load_business_rules, load_kpi_definitions
from .ingestion import IngestionPhase
from .output import OutputPhase
from .transformation import TransformationPhase

logger = get_logger(__name__)


class UnifiedPipeline:
    """
    Unified 4-Phase Pipeline Orchestrator

    Executes the complete data pipeline workflow:
    Input → Ingestion → Transformation → Calculation → Output → Dashboard
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the unified pipeline.

        Args:
            config_path: Path to pipeline.yml (optional, defaults to config/pipeline.yml)
        """
        logger.info("%s", "=" * 80)
        logger.info("UNIFIED PIPELINE ORCHESTRATOR v2.0")
        logger.info("%s", "=" * 80)

        # Load configurations
        self.config = PipelineConfig.load(config_path)
        self.business_rules = load_business_rules()
        self.kpi_definitions = load_kpi_definitions()

        # Initialize phases
        self.ingestion = IngestionPhase(self.config.ingestion)
        self.transformation = TransformationPhase(self.config.transformation, self.business_rules)
        self.calculation = CalculationPhase(self.config.calculation, self.kpi_definitions)
        self.output = OutputPhase(self.config.output)

        logger.info("All pipeline phases initialized successfully")

    def execute(self, input_path: Optional[Path] = None, mode: str = "full") -> Dict[str, Any]:
        """
        Execute the complete pipeline.

        Args:
            input_path: Path to input CSV file (optional)
            mode: Execution mode - 'full', 'validate', 'dry-run'

        Returns:
            Pipeline execution results
        """
        # Calculate deterministic run_id for idempotency
        if input_path and input_path.exists():

            data_hash = self._calculate_input_hash(input_path)
            run_id = f"{datetime.now().strftime('%Y%m%d')}_{data_hash[:8]}"
        else:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info("Starting pipeline execution (run_id: %s, mode: %s)", run_id, mode)

        # Create run directory
        run_dir = Path("logs") / "runs" / run_id

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
        }

        try:
            # PHASE 1: INGESTION
            separator = "=" * 80
            logger.info("\n%s", separator)
            logger.info("PHASE 1: INGESTION")
            logger.info("%s", separator)
            phase1_results = self.ingestion.execute(input_path=input_path, run_dir=run_dir)
            results["phases"]["ingestion"] = phase1_results

            if phase1_results["status"] != "success":
                raise Exception(f"Phase 1 failed: {phase1_results.get('error')}")

            if mode == "dry-run":
                logger.info("Dry-run mode: stopping after ingestion")
                return self._finalize_results(results, run_dir)

            # PHASE 2: TRANSFORMATION
            logger.info("\n%s", separator)
            logger.info("PHASE 2: TRANSFORMATION")
            logger.info("%s", separator)
            raw_data_path = (
                Path(phase1_results["output_path"]) if phase1_results.get("output_path") else None
            )
            phase2_results = self.transformation.execute(
                raw_data_path=raw_data_path, run_dir=run_dir
            )
            results["phases"]["transformation"] = phase2_results

            if phase2_results["status"] != "success":
                raise Exception(f"Phase 2 failed: {phase2_results.get('error')}")

            if mode == "validate":
                logger.info("Validate mode: stopping after transformation")
                return self._finalize_results(results, run_dir)

            # PHASE 3: CALCULATION
            logger.info("\n%s", separator)
            logger.info("PHASE 3: CALCULATION")
            logger.info("%s", separator)
            clean_data_path = (
                Path(phase2_results["output_path"]) if phase2_results.get("output_path") else None
            )
            phase3_results = self.calculation.execute(
                clean_data_path=clean_data_path, run_dir=run_dir
            )
            results["phases"]["calculation"] = phase3_results

            if phase3_results["status"] != "success":
                raise Exception(f"Phase 3 failed: {phase3_results.get('error')}")

            # PHASE 4: OUTPUT
            logger.info("\n%s", separator)
            logger.info("PHASE 4: OUTPUT")
            logger.info("%s", separator)
            phase4_results = self.output.execute(
                kpi_results=phase3_results.get("kpis", {}), run_dir=run_dir
            )
            results["phases"]["output"] = phase4_results

            if phase4_results["status"] != "success":
                raise Exception(f"Phase 4 failed: {phase4_results.get('error')}")

            return self._finalize_results(results, run_dir)

        except Exception as e:
            logger.error("Pipeline execution failed: %s", e)
            logger.error("%s", traceback.format_exc())

            results["status"] = "failed"
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

            return self._finalize_results(results, run_dir)

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
