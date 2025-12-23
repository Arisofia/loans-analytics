import os
import sys
from pathlib import Path

# Ensure repository modules can be imported when tests run from the repo root.
ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT,):
    sys.path.insert(0, str(path))

# Change working directory to repository root so relative file paths work
os.chdir(ROOT)

# Create sample CSV for tests if it doesn't exist
import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_sample_csv():
    """Create sample CSV file for tests if it doesn't exist."""
    csv_path = Path(ROOT) / "data_samples" / "abaco_portfolio_sample.csv"

    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Create sample data matching test expectations
        csv_content = """segment,measurement_date,dpd_90_plus_usd,total_receivable_usd,total_eligible_usd,cash_available_usd,par_90,collection_rate,delinquency_flag
Consumer,2025-01-31,32500,1000000,1000000,972000,3.25,97.2,1
Consumer,2025-02-28,32500,1000000,1000000,972000,3.25,97.2,1
SME,2025-01-31,32500,1000000,1000000,972000,3.25,97.2,1
SME,2025-02-28,32500,1000000,1000000,972000,3.25,97.2,1
"""
        csv_path.write_text(csv_content)
