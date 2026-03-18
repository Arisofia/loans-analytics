#!/usr/bin/env python3
"""
UNIFIED DATA PIPELINE - Main Entry Point

Execute the complete 4-phase pipeline:
1. Ingestion - Data collection
2. Transformation - Data cleaning
3. Calculation - KPI computation
4. Output - Results distribution

Usage:
    python scripts/data/run_data_pipeline.py
    python scripts/data/run_data_pipeline.py --input data/raw/loans.csv
    python scripts/data/run_data_pipeline.py --config config/pipeline.yml --mode validate
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.python.logging_config import get_logger, init_sentry  # noqa: E402
from backend.src.pipeline.orchestrator import (  # noqa: E402  # pylint: disable=wrong-import-order
    UnifiedPipeline,
)

init_sentry(service_name="data_pipeline")

logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Unified Data Pipeline - 4-Phase Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with default config
  python scripts/data/run_data_pipeline.py

  # Run with specific input file
  python scripts/data/run_data_pipeline.py --input data/raw/loans.csv

  # Validate configuration and data only
  python scripts/data/run_data_pipeline.py --mode validate

  # Dry run (ingestion only)
  python scripts/data/run_data_pipeline.py --mode dry-run

  # Use custom config file
  python scripts/data/run_data_pipeline.py --config config/custom_pipeline.yml
        """,
    )

    parser.add_argument(
        "--input", type=Path, help="Path to input CSV file (optional, can use API ingestion)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/pipeline.yml"),
        help="Path to pipeline configuration file (default: config/pipeline.yml)",
    )

    parser.add_argument(
        "--mode",
        choices=["full", "validate", "dry-run"],
        default="full",
        help=(
            "Execution mode: full (all phases), validate (stop after transformation), "
            "dry-run (ingestion only)"
        ),
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()

    logger.info("%s", "=" * 80)
    logger.info("UNIFIED PIPELINE EXECUTION STARTED")
    logger.info("%s", "=" * 80)
    logger.info("Config: %s", args.config)
    logger.info("Input: %s", args.input or "API ingestion")
    logger.info("Mode: %s", args.mode)
    logger.info("%s", "=" * 80)

    try:
        # Initialize pipeline
        pipeline = UnifiedPipeline(config_path=args.config if args.config.exists() else None)

        # Execute pipeline
        results = pipeline.execute(input_path=args.input, mode=args.mode)

        # Print summary
        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Status: {results['status'].upper()}")
        print(f"Run ID: {results['run_id']}")
        print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        print("\nPhase Results:")

        for phase_name, phase_results in results.get("phases", {}).items():
            status_symbol = "✅" if phase_results.get("status") == "success" else "❌"
            print(
                f"  {status_symbol} {phase_name.title()}: {phase_results.get('status', 'unknown')}"
            )

        print("=" * 80)

        # Exit with appropriate code
        if results["status"] == "success":
            print("\n✅ Pipeline execution completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Pipeline execution failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", e)
        print("\n❌ Error: Configuration file not found")
        print(f"Please create {args.config} with pipeline settings")
        print("\nSee UNIFIED_WORKFLOW.md for configuration details")
        sys.exit(1)

    except Exception as e:
        logger.error("Pipeline execution failed: %s", e, exc_info=True)
        print(f"\n❌ Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
