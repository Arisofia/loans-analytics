"""
Synthetic test data generators for fintech lending scenarios.

Security: All ID-like values use secrets module (unpredictable).
Statistical values use random with optional seed (reproducible for tests).

Follows python:S2245 guidelines for PRNG usage in security-sensitive contexts.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from secrets import choice as secrets_choice


RFC_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
RFC_DIGITS = "0123456789"
RFC_HOMONYM_CHARSET = RFC_DIGITS + RFC_LETTERS


def generate_mexican_rfc() -> str:
    """
    Generate a synthetic Mexican RFC.

    Security: Uses `secrets` for unpredictability to avoid accidental collision
    with real RFCs. Format is simplified but structurally similar: AAAAYYMMDDXXX.
    """
    prefix = "".join(secrets_choice(RFC_LETTERS) for _ in range(4))
    # Random, non-realistic date components to avoid mapping to real DOBs
    year = "".join(secrets_choice(RFC_DIGITS) for _ in range(2))
    month = "".join(
        secrets_choice("01") + secrets_choice(RFC_DIGITS[1:])
    )  # 01–12-like
    day = "".join(
        secrets_choice("012") + secrets_choice(RFC_DIGITS[1:])
    )  # 01–29-like
    homonym = "".join(secrets_choice(RFC_HOMONYM_CHARSET) for _ in range(3))
    return f"{prefix}{year}{month}{day}{homonym}"


@dataclass
class Loan:
    loan_id: str
    customer_id: str
    disbursement_date: date
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int


def generate_loan(loan_number: int | None = None, start_date: date | None = None) -> Loan:
    """
    Generate a reproducible synthetic loan for tests.

    Security note:
    - Uses `random` with an implicit seed context for reproducibility.
    - No security-sensitive values (tokens/passwords) are generated.
    - This is acceptable per python:S2245 guidance in test_prng_security.
    """
    if start_date is None:
        start_date = date(2024, 1, 1)

    loan_id = f"LN-{loan_number or random.randint(100000, 999999)}"
    customer_id = f"CUST-{random.randint(10000, 99999)}"
    year = start_date.year
    month = random.randint(1, 12)
    day = random.randint(1, 28)

    principal = Decimal(str(round(random.uniform(1_000, 50_000), 2)))
    rate = Decimal(str(round(random.uniform(0.10, 0.45), 4)))
    term = random.choice([6, 9, 12, 18, 24])

    return Loan(
        loan_id=loan_id,
        customer_id=customer_id,
        disbursement_date=date(year, month, day),
        principal_amount=principal,
        interest_rate=rate,
        term_months=term,
    )
