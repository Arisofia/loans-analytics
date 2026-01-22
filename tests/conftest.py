import os
import sys
from pathlib import Path

import pytest
from python.testing.db_manager import DBManager

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)


@pytest.fixture(scope="session")
def analytics_test_env(tmp_path_factory):
    """Analytics test environment with mocked integrations."""
    output_dir = tmp_path_factory.mktemp("output")
    dataset_path = ROOT / "tests" / "data" / "archives" / "sample_small.csv"

    return {
        "output_dir": output_dir,
        "dataset_path": dataset_path,
    }


@pytest.fixture
def analytics_baseline_kpis():
    """Load baseline KPI values for comparison."""
    return ROOT / "tests" / "fixtures" / "baseline_kpis.json"


@pytest.fixture
def minimal_config():
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
                "calculation": {},
                "outputs": {},
            },
        },
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
    }


def pytest_configure(config):
    """
    Configure Pytest to add custom markers.

    The 'db' marker is used to indicate that a test requires a database.
    """
    # Add custom marker for database tests
    config.addinivalue_line("markers", "db: requires database")

    # Add docstring for the custom marker
    config.addinivalue_line(
        "markers",
        "db: Mark test as requiring a database.\n"
        "      This marker is used to indicate that a test requires a database.\n"
        "      The test will be skipped if the DATABASE_URL environment variable is not set.",
    )


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
