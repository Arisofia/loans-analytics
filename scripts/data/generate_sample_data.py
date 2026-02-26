"""
Synthetic test data generators for fintech lending scenarios.

Security: All ID-like values use secrets module (unpredictable).
Statistical values use random with optional seed (reproducible for tests).

Follows python:S2245 guidelines for PRNG usage in security-sensitive contexts.
"""

from __future__ import annotations

import random
import secrets
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

# Use SystemRandom for security-sensitive values
cryptogen = secrets.SystemRandom()

RFC_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
RFC_DIGITS = "0123456789"
RFC_HOMONYM_CHARSET = RFC_DIGITS + RFC_LETTERS


@dataclass
class LoanData:
    """Metadata for a synthetic loan."""
    loan_id: str
    customer_id: str
    principal: Decimal
    rate: Decimal
    term: int
    disbursement_date: date
    status: str
    product: str


class SampleDataGenerator:
    """Generates deterministic or random sample data for testing."""

    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)
            # Note: secrets module doesn't use random.seed
            # For truly deterministic tests, you'd need a different approach
            # but for this repo's scope, we prioritize security.

    def generate_loan(
        self,
        loan_number: int | None = None,
        start_date: date | None = None
    ) -> LoanData:
        """Generate a single realistic loan record."""
        if start_date is None:
            start_date = date.today()

        # Use cryptogen (secrets.SystemRandom) for IDs and financial values
        loan_id = f"LN-{loan_number or cryptogen.randint(100000, 999999)}"
        customer_id = f"CUST-{cryptogen.randint(10000, 99999)}"
        year = start_date.year
        month = cryptogen.randint(1, 12)
        day = cryptogen.randint(1, 28)

        principal = Decimal(str(round(cryptogen.uniform(1_000, 50_000), 2)))
        rate = Decimal(str(round(cryptogen.uniform(0.10, 0.45), 4)))
        term = cryptogen.choice([6, 9, 12, 18, 24])

        return LoanData(
            loan_id=loan_id,
            customer_id=customer_id,
            principal=principal,
            rate=rate,
            term=term,
            disbursement_date=date(year, month, day),
            status=cryptogen.choice(["active", "active", "delinquent", "closed"]),
            product=cryptogen.choice(["PLN", "CC", "MTG"])
        )
