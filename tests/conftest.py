import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from tests.db_manager import DBManager

# Ensure repository modules can be imported when tests run from the repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

# Change working directory to repository root so relative file paths work
os.chdir(ROOT)


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


@pytest.fixture
def minimal_config() -> Dict[str, Any]:
    """Minimal pipeline config for testing."""
    return {
        "pipeline": {
            "phases": {
                "ingestion": {
                    "validation": {
                        "strict": False,
                        "required_columns": [
                            "total_receivable_usd",
                            "total_eligible_usd",
                            "discounted_balance_usd",
                        ],
                        "numeric_columns": [
                            "total_receivable_usd",
                            "total_eligible_usd",
                            "discounted_balance_usd",
                            "cash_available_usd",
                            "dpd_0_7_usd",
                            "dpd_7_30_usd",
                            "dpd_30_60_usd",
                            "dpd_60_90_usd",
                            "dpd_90_plus_usd",
                        ],
                        "date_columns": ["measurement_date"],
                    },
                    "deduplication": {"enabled": False},
                },
                "transformation": {
                    "normalization": {
                        "lowercase_columns": True,
                        "strip_whitespace": True,
                    },
                    "null_handling": {
                        "strategy": "fill_zero",
                        "columns": [],
                    },
                    "outlier_detection": {
                        "enabled": False,
                    },
                    "pii_masking": {
                        "enabled": False,
                    },
                },
            },
        },
        "cascade": {
            "http": {
                "retry": {
                    "max_retries": 1,
                    "backoff_seconds": 0.1,
                },
                "rate_limit": {
                    "max_requests_per_minute": 60,
                },
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "reset_seconds": 60,
                },
            },
        },
    }


def pytest_configure(config):
    config.addinivalue_line("markers", "db: requires database")


# === Database fixtures for backend tests ===
@pytest.fixture(scope="session")
def db_setup():
    """Session-scoped fixture that ensures a clean, deterministic DB baseline.

    - Requires `DATABASE_URL` to be set in the environment (use .env for local dev)
    - Wipes tables and seeds deterministic KPI rows used by sync tests
    """
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")

    manager = DBManager()
    manager.wipe_database()
    manager.seed_kpi_data()
    yield manager
    # Optional teardown after the full test session. Uncomment if desired:
    # manager.wipe_database()


@pytest.fixture(scope="function")
def db_reset(db_setup):
    """Reset DB between tests when a test needs a fresh state."""
    db_setup.wipe_database()
    db_setup.seed_kpi_data()
    yield
    db_setup.wipe_database()
