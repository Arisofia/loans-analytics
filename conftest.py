import random
import inspect
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env so integration tests (RUN_REAL_SUPABASE_TESTS, etc.) are not skipped locally
load_dotenv = None
try:
    from dotenv import load_dotenv

except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    _env_file = ROOT / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=False)


def _build_portfolio(n: int = 50, seed: int = 42) -> pd.DataFrame:
    """Deterministic realistic lending portfolio DataFrame."""
    rng = random.Random(seed)
    today = date(2026, 3, 26)
    _status_pool = (
        ["current"] * 35
        + ["30-59 days past due"] * 6
        + ["60-89 days past due"] * 4
        + ["90+ days past due"] * 3
        + ["default"] * 2
    )
    statuses = (_status_pool * ((n // len(_status_pool)) + 1))[:n]
    _dpd_by_status = {
        "current": 0,
        "30-59 days past due": lambda: rng.randint(30, 59),
        "60-89 days past due": lambda: rng.randint(60, 89),
        "90+ days past due": lambda: rng.randint(90, 179),
        "default": lambda: rng.randint(180, 365),
    }
    records = []
    for i, status in enumerate(statuses):
        principal = round(rng.uniform(2_000, 48_000), 2)
        dpd_val = _dpd_by_status[status]
        dpd = 0 if status == "current" else dpd_val()
        disb_date = today - timedelta(days=rng.randint(60, 720))
        records.append(
            {
                "loan_id": f"LN-{i + 1:04d}",
                "borrower_id": f"B-{(i % 40) + 1:03d}",
                "loan_amount": principal,
                "principal_balance": round(principal * rng.uniform(0.30, 0.95), 2),
                "outstanding_loan_value": round(principal * rng.uniform(0.30, 0.95), 2),
                "appraised_value": round(principal * rng.uniform(1.1, 2.5), 2),
                "borrower_income": round(rng.uniform(18_000, 120_000), 2),
                "monthly_debt": round(rng.uniform(300, 3_000), 2),
                "interest_rate": round(rng.uniform(0.18, 0.45), 4),
                "interest_rate_apr": round(rng.uniform(0.18, 0.45), 4),
                "loan_status": status,
                "days_past_due": dpd,
                "days_in_default": dpd if status == "default" else 0,
                "term_months": rng.choice([6, 9, 12, 18, 24]),
                "origination_fee": round(principal * rng.uniform(0.01, 0.03), 2),
                "origination_fee_taxes": round(principal * 0.016 * 0.16, 2),
                "total_scheduled": round(principal * rng.uniform(0.08, 0.15), 2),
                "last_payment_amount": round(principal * rng.uniform(0.05, 0.12), 2),
                "tpv": round(rng.uniform(50_000, 500_000), 2),
                "disbursement_date": disb_date.isoformat(),
                "origination_date": disb_date.isoformat(),
                "pagador": f"P-{(i % 15) + 1:02d}",
            }
        )
    return pd.DataFrame(records)


@pytest.fixture(scope="session")
def realistic_portfolio_df() -> pd.DataFrame:
    """Session-scoped 50-loan realistic lending portfolio (deterministic, seed=42)."""
    return _build_portfolio(n=50, seed=42)


@pytest.fixture(scope="session")
def realistic_loan_records() -> list:
    """Session-scoped list of 25 LoanRecord-compatible dicts for analytics endpoints."""
    from backend.python.apps.analytics.api.models import LoanRecord

    rng = random.Random(99)
    today = date(2026, 3, 26)
    statuses = (
        ["current"] * 17
        + ["30-59 days past due"] * 3
        + ["60-89 days past due"] * 2
        + ["90+ days past due"] * 2
        + ["default"] * 1
    )
    records = []
    for i, status in enumerate(statuses):
        principal = round(rng.uniform(3_000, 45_000), 2)
        dpd: float = 0.0
        if status == "30-59 days past due":
            dpd = float(rng.randint(30, 59))
        elif status == "60-89 days past due":
            dpd = float(rng.randint(60, 89))
        elif status == "90+ days past due":
            dpd = float(rng.randint(90, 179))
        elif status == "default":
            dpd = float(rng.randint(180, 365))
        disb_date = today - timedelta(days=rng.randint(90, 600))
        records.append(
            LoanRecord(
                id=f"LN-R{i + 1:03d}",
                loan_amount=principal,
                principal_balance=round(principal * rng.uniform(0.30, 0.95), 2),
                appraised_value=round(principal * rng.uniform(1.1, 2.5), 2),
                borrower_income=round(rng.uniform(20_000, 110_000), 2),
                monthly_debt=round(rng.uniform(400, 2_800), 2),
                interest_rate=round(rng.uniform(0.18, 0.45), 4),
                loan_status=status,
                days_past_due=dpd,
                term_months=float(rng.choice([6, 9, 12, 18, 24])),
                origination_fee=round(principal * rng.uniform(0.01, 0.03), 2),
                origination_fee_taxes=round(principal * 0.016 * 0.16, 2),
                total_scheduled=round(principal * rng.uniform(0.08, 0.15), 2),
                last_payment_amount=round(principal * rng.uniform(0.05, 0.12), 2),
                tpv=round(rng.uniform(60_000, 450_000), 2),
                borrower_id=f"B-{(i % 20) + 1:03d}",
                origination_date=disb_date,
            )
        )
    return records


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Run async tests without requiring pytest-asyncio plugin."""
    test_function = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_function):
        kwargs = {
            name: pyfuncitem.funcargs[name]
            for name in pyfuncitem._fixtureinfo.argnames
            if name in pyfuncitem.funcargs
        }
        asyncio.run(test_function(**kwargs))
        return True
    return None
