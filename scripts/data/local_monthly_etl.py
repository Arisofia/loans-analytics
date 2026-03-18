#!/usr/bin/env python3
"""CLI entry point for the local monthly star-schema ETL.

Thin wrapper around :func:`src.zero_cost.local_migration_etl.main`.
All business logic lives in the module; this script only adds the project
root to ``sys.path`` and delegates execution.

Usage::

    python scripts/data/local_monthly_etl.py \\
        --loan-tape-dir data/raw \\
        --snapshot-month 2026-01-31 \\
        --output-dir exports/local_star
"""

import logging
import sys
from pathlib import Path

# Add project root to path so the package can be imported when running
# this script directly (mirrors the pattern used by run_data_pipeline.py).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

from backend.src.zero_cost.local_migration_etl import main  # noqa: E402

if __name__ == "__main__":
    main()

