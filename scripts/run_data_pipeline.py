#!/usr/bin/env python3
"""
CLI wrapper for the unified data pipeline orchestrator.

This script is the primary entry point for running the 4-phase ETL pipeline:
1. Ingestion (CSV/Supabase data loading with validation)
2. Transformation (PII masking, data normalization)
3. Calculation (19 KPI metrics across 6 categories)
4. Output (Multi-format export: Parquet/CSV/JSON)

Invoked by:
- CI/CD workflows (daily-ingest.yml, agents_unified_pipeline.yml, unified-tests.yml)
- Local development: python scripts/run_data_pipeline.py --input data/raw/sample_loans.csv
- Validation mode: python scripts/run_data_pipeline.py --mode validate
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.orchestrator import UnifiedPipeline


def main():
    """CLI entry point for the unified pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="Run the unified 4-phase data pipeline (Ingestion → Transformation → Calculation → Output)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/sample_loans.csv",
        help="Path to input CSV file (default: data/raw/sample_loans.csv)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["validate", "dry-run", "full"],
        default="full",
        help="Execution mode: validate (check config only), dry-run (ingestion only), full (all phases)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/pipeline.yml",
        help="Path to pipeline config file (default: config/pipeline.yml)",
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = UnifiedPipeline(config_path=Path(args.config))

    # Execute pipeline
    result = pipeline.execute(
        input_path=Path(args.input) if args.input else None, mode=args.mode
    )

    # Return exit code based on result
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
