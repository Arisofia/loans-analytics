"""
Test Data Generators for TestCraftPro v2.0
Generate realistic synthetic test data for various testing scenarios.

SECURITY NOTE (python:S2245 - PRNG Usage):
These generators create SYNTHETIC TEST DATA with reproducible randomness (seed parameter).
Most random operations use the standard `random` module which is NOT cryptographically secure,
but this is ACCEPTABLE because:
1. All data is synthetic/test data, not production data
2. Reproducibility (via seed) is required for consistent test scenarios
3. EXCEPTION: PII like SSNs use `secrets` module for security even in test data

Security-sensitive operations that use secrets module:
- SSN generation in UserDataGenerator (see _generate_ssn)

Usage:
    from test_data_generators import LoanDataGenerator, UserDataGenerator

    # Generate loan data
    loan_gen = LoanDataGenerator(seed=42)
    loans = loan_gen.generate_loans(count=1000, output_format='csv')

    # Generate user data
    user_gen = UserDataGenerator(seed=42)
    users = user_gen.generate_users(count=100, mask_pii=True)
"""

from __future__ import annotations

import csv
import json
import random
import secrets
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from io import StringIO
from typing import Literal


class LoanDataGenerator:
    """Generate synthetic loan portfolio data for testing"""

    def __init__(self, seed: int | None = 42):
        """
        Initialize generator with optional seed for reproducibility

        Args:
            seed: Random seed for reproducible data generation
        """
        # Security: python:S2245 - Use of `random` is acceptable for synthetic test data.
        # PII-like fields (SSN) use `secrets` for CSPRNG.
        self._rng = random.Random(seed)

    def generate_loans(
        self, count: int = 1000, output_format: Literal["dict", "csv", "json", "sql"] = "dict"
    ) -> list[dict] | str:
        """
        Generate synthetic loan data with realistic distributions

        Args:
            count: Number of loans to generate
            output_format: Output format ('dict', 'csv', 'json', or 'sql')

        Returns:
            Generated data in specified format
        """
        loans = []

        # Realistic distributions
        statuses = ["current", "late", "default", "paid_off"]
        status_weights = [0.75, 0.15, 0.05, 0.05]

        segments = ["consumer", "sme", "auto"]
        segment_weights = [0.60, 0.30, 0.10]

        for i in range(count):
            status = self._rng.choices(statuses, weights=status_weights)[0]
            segment = self._rng.choices(segments, weights=segment_weights)[0]

            # Segment-specific parameters
            if segment == "consumer":
                amount_range = (1000, 25000)
                apr_range = (0.18, 0.35)
                term_options = [6, 12, 24, 36]
            elif segment == "sme":
                amount_range = (10000, 100000)
                apr_range = (0.12, 0.25)
                term_options = [12, 24, 36, 48, 60]
            else:  # auto
                amount_range = (5000, 50000)
                apr_range = (0.05, 0.15)
                term_options = [24, 36, 48, 60, 72]

            amount = Decimal(str(self._rng.uniform(*amount_range))).quantize(Decimal("0.01"))
            apr = Decimal(str(self._rng.uniform(*apr_range))).quantize(Decimal("0.0001"))
            term_months = self._rng.choice(term_options)

            origination_date = self._random_date(365)
            dpd = self._calculate_dpd(status)

            # Calculate outstanding balance
            if status == "paid_off":
                outstanding = Decimal("0.00")
            else:
                outstanding = amount * Decimal(str(self._rng.uniform(0.3, 1.0)))
                outstanding = outstanding.quantize(Decimal("0.01"))

            loan = {
                "loan_id": f"LOAN-{i+1:06d}",
                "borrower_id": f"BORR-{self._rng.randint(1, count//3):06d}",
                "amount": str(amount),
                "apr": str(apr),
                "term_months": term_months,
                "status": status,
                "dpd": dpd,
                "origination_date": origination_date.strftime("%Y-%m-%d"),
                "outstanding_balance": str(outstanding),
                "segment": segment,
                "monthly_payment": str(self._calculate_monthly_payment(amount, apr, term_months)),
            }
            loans.append(loan)

        # Format output
        if output_format == "dict":
            return loans
        elif output_format == "csv":
            return self._to_csv(loans)
        elif output_format == "json":
            return json.dumps(loans, indent=2)
        elif output_format == "sql":
            return self._to_sql(loans)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _calculate_dpd(self, status: str) -> int:
        """Calculate Days Past Due based on loan status"""
        if status == "current":
            return 0
        if status == "late":
            return self._rng.randint(1, 89)
        if status == "default":
            return self._rng.randint(90, 180)
        return 0  # paid_off

    def _calculate_monthly_payment(self, principal: Decimal, apr: Decimal, term: int) -> Decimal:
        """Calculate monthly payment amount"""
        if apr == 0:
            return (principal / term).quantize(Decimal("0.01"))

        monthly_rate = apr / 12
        payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** term)
            / ((1 + monthly_rate) ** term - 1)
        )
        return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _random_date(self, days_back: int) -> datetime:
        """Generate random date within last N days"""
        return datetime.now() - timedelta(days=self._rng.randint(1, days_back))

    def _to_csv(self, loans: list[dict]) -> str:
        """Convert to CSV format"""
        output = StringIO()
        if loans:
            writer = csv.DictWriter(output, fieldnames=loans[0].keys())
            writer.writeheader()
            writer.writerows(loans)
        return output.getvalue()

    def _to_sql(self, loans: list[dict]) -> str:
        """Convert to SQL INSERT statements"""
        if not loans:
            return ""

        table_name = "loans"
        fields = ", ".join(loans[0].keys())

        inserts = []
        for loan in loans:
            values = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in loan.values())
            inserts.append(f"INSERT INTO {table_name} ({fields}) VALUES ({values});")

        return "\n".join(inserts)


class UserDataGenerator:
    """Generate synthetic user/customer data with PII masking"""

    def __init__(self, seed: int | None = 42):
        self._rng = random.Random(seed)
        self.first_names = ["John", "Jane", "Maria", "Carlos", "Ana", "Miguel", "Sofia", "Diego"]
        self.last_names = ["Smith", "Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez"]

    def generate_users(
        self,
        count: int = 100,
        mask_pii: bool = True,
        output_format: Literal["dict", "csv", "json"] = "dict",
    ) -> list[dict] | str:
        """
        Generate synthetic user data

        Args:
            count: Number of users to generate
            mask_pii: Whether to mask PII (SSN, email)
            output_format: Output format

        Returns:
            Generated user data
        """
        users = []

        for i in range(count):
            first = self._rng.choice(self.first_names)
            last = self._rng.choice(self.last_names)

            email = f"{first.lower()}.{last.lower()}{i}@test.com"
            if mask_pii:
                email = "masked@example.test"

            # SSN generation uses secrets module for security even in test data
            # Security: python:S2245 - Uses CSPRNG (secrets) instead of PRNG (random)
            ssn = (
                f"{secrets.randbelow(899) + 1:03d}-"
                f"{secrets.randbelow(90) + 10:02d}-"
                f"{secrets.randbelow(9000) + 1000:04d}"
            )
            if mask_pii:
                ssn = f"***-**-{ssn[-4:]}"

            user = {
                "user_id": f"USER-{i+1:06d}",
                "first_name": first,
                "last_name": last,
                "email": email,
                "ssn": ssn,
                "phone": f"+1-555-{self._rng.randint(100, 999)}-{self._rng.randint(1000, 9999)}",
                "created_at": (datetime.now() - timedelta(days=self._rng.randint(1, 730))).strftime(
                    "%Y-%m-%d"
                ),
                "status": self._rng.choice(["active", "inactive", "suspended"]),
            }
            users.append(user)

        if output_format == "dict":
            return users
        elif output_format == "csv":
            output = StringIO()
            if users:
                writer = csv.DictWriter(output, fieldnames=users[0].keys())
                writer.writeheader()
                writer.writerows(users)
            return output.getvalue()
        elif output_format == "json":
            return json.dumps(users, indent=2)


class PaymentDataGenerator:
    """Generate synthetic payment transaction data"""

    def __init__(self, seed: int | None = 42):
        self._rng = random.Random(seed)

    def generate_payments(
        self,
        loan_ids: list[str],
        payments_per_loan: tuple[int, int] = (1, 12),
        output_format: Literal["dict", "csv", "json"] = "dict",
    ) -> list[dict] | str:
        """
        Generate payment transactions for loans

        Args:
            loan_ids: List of loan IDs to generate payments for
            payments_per_loan: (min, max) payments per loan
            output_format: Output format

        Returns:
            Generated payment data
        """
        payments = []
        payment_id = 1

        for loan_id in loan_ids:
            num_payments = self._rng.randint(*payments_per_loan)

            for _i in range(num_payments):
                amount = Decimal(str(self._rng.uniform(100, 2000))).quantize(Decimal("0.01"))

                if self._rng.random() < 0.05:
                    status = self._rng.choice(["pending", "failed"])
                else:
                    status = "completed"

                payment = {
                    "payment_id": f"PAY-{payment_id:08d}",
                    "loan_id": loan_id,
                    "amount": str(amount),
                    "payment_date": (
                        datetime.now() - timedelta(days=self._rng.randint(1, 365))
                    ).strftime("%Y-%m-%d"),
                    "payment_method": self._rng.choice(["bank_transfer", "card", "check", "cash"]),
                    "status": status,
                }
                payments.append(payment)
                payment_id += 1

        if output_format == "dict":
            return payments
        elif output_format == "csv":
            output = StringIO()
            if payments:
                writer = csv.DictWriter(output, fieldnames=payments[0].keys())
                writer.writeheader()
                writer.writerows(payments)
            return output.getvalue()
        elif output_format == "json":
            return json.dumps(payments, indent=2)


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    # Generate loan data
    print("Generating loan data...")
    loan_gen = LoanDataGenerator(seed=42)
    loans = loan_gen.generate_loans(count=1000, output_format="dict")
    print(f"Generated {len(loans)} loans")

    # Ensure output directory exists
    out_dir = Path("data/test")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    csv_data = loan_gen.generate_loans(count=1000, output_format="csv")
    with open(out_dir / "loans_test_data.csv", "w", encoding="utf-8") as f:
        f.write(str(csv_data))
    print("Saved to data/test/loans_test_data.csv")

    # Generate user data with PII masking
    print("\nGenerating user data...")
    user_gen = UserDataGenerator(seed=42)
    users = user_gen.generate_users(count=100, mask_pii=True, output_format="dict")
    print(f"Generated {len(users)} users (PII masked)")

    # Generate payment data
    print("\nGenerating payment data...")
    loan_ids = [
        str(loan["loan_id"])
        for loan in loans[:100]
        if isinstance(loan, dict) and "loan_id" in loan
    ]
    payment_gen = PaymentDataGenerator(seed=42)
    payments = payment_gen.generate_payments(loan_ids, payments_per_loan=(3, 12))
    print(f"Generated {len(payments)} payments")
