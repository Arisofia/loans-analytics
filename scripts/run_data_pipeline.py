#!/usr/bin/env python3
"""
CLI wrapper for the unified data pipeline orchestrator.

This script is the primary entry point for running the 4-phase ETL pipeline:
1. Ingestion (CSV/Supabase data loading with validation)
2. Transformation (PII masking, data normalization)
3. Calculation (19 KPI metrics across 6 categories)
4. Output (Multi-format export: Parquet/CSV/JSON)

The actual implementation is in src.pipeline.orchestrator.main().

Invoked by:
- CI/CD workflows (daily-ingest.yml, agents_unified_pipeline.yml)
- Local development: python scripts/run_data_pipeline.py
- Validation mode: python scripts/run_data_pipeline.py --mode validate
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.orchestrator import main

if __name__ == "__main__":
    sys.exit(main())
