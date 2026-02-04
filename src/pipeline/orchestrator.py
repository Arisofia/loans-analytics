"""
UNIFIED PIPELINE ORCHESTRATOR

Coordinates all 4 phases of the data pipeline:
1. Ingestion
2. Transformation
3. Calculation
4. Output

NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/run_data_pipeline.py
"""

import argparse
import hashlib
import json
import sys
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
                error_msg = f"Phase 1 (Ingestion) failed: {phase1_results.get('error')}"
                raise RuntimeError(error_msg)

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
                error_msg = f"Phase 2 (Transformation) failed: {phase2_results.get('error')}"
                raise RuntimeError(error_msg)

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
                error_msg = f"Phase 3 (Calculation) failed: {phase3_results.get('error')}"
                raise RuntimeError(error_msg)

            # PHASE 4: OUTPUT
            logger.info("\n%s", separator)
            logger.info("PHASE 4: OUTPUT")
            logger.info("%s", separator)
            phase4_results = self.output.execute(
                kpi_results=phase3_results.get("kpis", {}), run_dir=run_dir
            )
            results["phases"]["output"] = phase4_results

            if phase4_results["status"] != "success":
                error_msg = f"Phase 4 (Output) failed: {phase4_results.get('error')}"
                raise RuntimeError(error_msg)

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
            "Unified 4-Phase Data Pipeline "
            "(Ingestion → Transformation → Calculation → Output)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Run full pipeline with CSV input
  python scripts/run_data_pipeline.py --input data/raw/sample_loans.csv

  # Validation mode (stop after transformation)
  python scripts/run_data_pipeline.py --mode validate

  # Dry-run mode (stop after ingestion)
  python scripts/run_data_pipeline.py --mode dry-run

  # Custom config file
  python scripts/run_data_pipeline.py --config config/custom_pipeline.yml
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
        choices=["full", "validate", "dry-run"],
        default="full",
        help=(
            "Execution mode: full (all phases), "
            "validate (stop after transformation), "
            "dry-run (stop after ingestion)"
        ),
    )

    args = parser.parse_args()

    try:
        # Initialize pipeline
        config_path = Path(args.config) if args.config else None
        pipeline = UnifiedPipeline(config_path=config_path)

        # Execute pipeline
        input_path = Path(args.input) if args.input else None
        results = pipeline.execute(input_path=input_path, mode=args.mode)

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
