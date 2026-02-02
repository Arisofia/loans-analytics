#!/usr/bin/env python3
"""Generate realistic sample loan data for Abaco Factoring.

Creates realistic loan portfolio data with proper distributions:
- Amounts: Log-normal ($10K-$500K, median ~$75K)
- Rates: Normal (28%-45%, mean 34%)
- Status: Realistic distribution (70% current, 20% delinquent, 5% default, 5% paid)
- Names: Real Spanish names
- Dates: Realistic vintages (6-36 months old)

Usage:
    python scripts/generate_sample_data.py --output data/raw/sample_loans.csv --count 800
    python scripts/generate_sample_data.py --start-date 2023-01-01 --end-date 2024-12-31
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import secrets
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

# Realistic Spanish names for borrowers
FIRST_NAMES = [
    "Carlos",
    "María",
    "José",
    "Ana",
    "Francisco",
    "Carmen",
    "Antonio",
    "Isabel",
    "Manuel",
    "Dolores",
    "David",
    "Laura",
    "Javier",
    "Marta",
    "Miguel",
    "Elena",
    "Pedro",
    "Rosa",
    "Fernando",
    "Patricia",
    "Rafael",
    "Teresa",
    "Luis",
    "Sofía",
    "Ángel",
    "Cristina",
    "Jorge",
    "Lucía",
    "Ramón",
    "Pilar",
    "Diego",
    "Beatriz",
]

LAST_NAMES = [
    "García",
    "Rodríguez",
    "González",
    "Fernández",
    "López",
    "Martínez",
    "Sánchez",
    "Pérez",
    "Gómez",
    "Martín",
    "Jiménez",
    "Ruiz",
    "Hernández",
    "Díaz",
    "Moreno",
    "Muñoz",
    "Álvarez",
    "Romero",
    "Alonso",
    "Gutiérrez",
    "Navarro",
    "Torres",
    "Domínguez",
    "Vázquez",
    "Ramos",
    "Gil",
    "Ramírez",
    "Serrano",
    "Blanco",
    "Suárez",
]

# Regions in Mexico (Abaco's market)
REGIONS = [
    "Ciudad de México",
    "Guadalajara",
    "Monterrey",
    "Puebla",
    "Tijuana",
    "León",
    "Querétaro",
    "Mérida",
    "Aguascalientes",
    "Hermosillo",
]


def generate_mexican_rfc() -> str:
    """Generate realistic Mexican RFC (Registro Federal de Contribuyentes)."""
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
    digits = "".join(random.choices("0123456789", k=6))
    suffix = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    return f"{letters}{digits}{suffix}"


def _determine_payment_status(status: str, month: int, current_month: int) -> str:
    """Determine payment status based on loan status and month."""
    if status == "current" or (status == "delinquent" and month < current_month - 2):
        return "paid" if random.random() > 0.05 else "late"
    if status == "delinquent":
        return random.choice(["late", "missed"])
    if status == "defaulted":
        return "missed" if month >= current_month - 6 else "paid"
    return "paid"  # paid_off


def _calculate_days_late(payment_status: str, status: str) -> int:
    """Calculate days late based on payment status."""
    if payment_status == "paid":
        return 0
    if status == "delinquent" and payment_status == "late":
        return random.randint(30, 90)
    if status != "defaulted" and payment_status == "late":
        return random.randint(1, 15)
    return 0


def _calculate_amount_paid(payment_status: str) -> Decimal:
    """Calculate amount paid based on payment status using Decimal for precision."""
    if payment_status == "missed":
        return Decimal("0.00")
    # Generate random amount between 5000 and 15000 with 2 decimal places
    amount_float = random.uniform(5000, 15000)
    return Decimal(str(amount_float)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_payment_history(
    term_months: int, current_month: int, status: str
) -> list[dict[str, Any]]:
    """Generate realistic payment history."""
    history = []
    for month in range(1, min(current_month + 1, term_months + 1)):
        payment_status = _determine_payment_status(status, month, current_month)
        days_late = _calculate_days_late(payment_status, status)
        amount_paid = _calculate_amount_paid(payment_status)

        history.append(
            {
                "month": month,
                "status": payment_status,
                "days_late": days_late,
                "amount_paid": amount_paid,
            }
        )
    return history


def generate_loan(loan_id: int, origination_date: datetime) -> dict[str, Any]:
    """Generate a single realistic loan record."""
    # Amount: log-normal distribution (median ~$75K, range $10K-$500K)
    # Use Decimal for financial accuracy
    amount_float = random.lognormvariate(11.2, 0.7)
    amount_float = min(500000, max(10000, amount_float))
    amount = Decimal(str(amount_float)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Interest rate: normal distribution (mean 34%, std 4%)
    # Store as Decimal percentage (e.g., Decimal("34.50") for 34.50%)
    rate_float = random.gauss(34, 4)
    rate_float = min(45, max(28, rate_float))
    rate = Decimal(str(rate_float)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Term: common terms (12, 18, 24, 36 months)
    term_months = random.choices([12, 18, 24, 36], weights=[0.2, 0.3, 0.3, 0.2])[0]

    # Status: realistic distribution
    status = random.choices(
        ["current", "delinquent", "defaulted", "paid_off"], weights=[0.70, 0.20, 0.05, 0.05]
    )[0]

    # Calculate current month
    months_elapsed = (datetime.now() - origination_date).days // 30
    current_month = min(months_elapsed, term_months)

    # Payment history
    payment_history = generate_payment_history(term_months, current_month, status)

    # Risk score based on status
    if status == "current":
        risk_score = random.randint(600, 850)
    elif status == "delinquent":
        risk_score = random.randint(500, 650)
    elif status == "defaulted":
        risk_score = random.randint(300, 550)
    else:  # paid_off
        risk_score = random.randint(650, 850)

    # Borrower details
    first_name = random.choice(FIRST_NAMES)
    last_name = f"{random.choice(LAST_NAMES)} {random.choice(LAST_NAMES)}"
    company_name = f"{random.choice(['Comercial', 'Distribuidora', 'Importadora', 'Exportadora'])} {last_name.split()[0]}"

    borrower_id = f"BRW{loan_id:06d}"

    # Convert Decimal objects to strings for JSON serialization
    payment_history_serializable = [
        {
            "month": p["month"],
            "status": p["status"],
            "days_late": p["days_late"],
            "amount_paid": str(p["amount_paid"]),  # Decimal → string for JSON
        }
        for p in payment_history
    ]

    return {
        "loan_id": f"ABF{loan_id:06d}",
        "borrower_id": borrower_id,  # Required for validation
        "borrower_name": company_name,
        "borrower_contact": f"{first_name} {last_name}",
        "borrower_email": (
            f"{first_name.lower()}.{last_name.split()[0].lower()}"
            f"@{company_name.replace(' ', '').lower()}.mx"
        ),
        "borrower_id_number": generate_mexican_rfc(),
        "amount": str(amount),  # Convert Decimal to string for CSV
        "principal_amount": str(amount),
        "rate": str(rate / Decimal("100")),  # Convert percentage to decimal (e.g., 0.3450)
        "interest_rate": str(rate),  # Keep as percentage string
        "term_months": term_months,
        "origination_date": origination_date.strftime("%Y-%m-%d"),
        "status": status,  # Match expected column name
        "current_status": status,
        "payment_history_json": json.dumps(payment_history_serializable),
        "risk_score": risk_score,
        "region": secrets.choice(REGIONS),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate realistic sample loan data for Abaco Factoring"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/sample_loans.csv",
        help="Output CSV file path (default: data/raw/sample_loans.csv)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=800,
        help="Number of loans to generate (default: 800)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2023-01-01",
        help="Earliest origination date (YYYY-MM-DD, default: 2023-01-01)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="Latest origination date (YYYY-MM-DD, default: 2024-12-31)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    date_range = (end_date - start_date).days

    # Generate loans
    loans = []
    for i in range(1, args.count + 1):
        origination_date = start_date + timedelta(days=random.randint(0, date_range))
        loan = generate_loan(i, origination_date)
        loans.append(loan)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    if loans:
        fieldnames = loans[0].keys()
        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(loans)

    print(f"✅ Generated {len(loans)} realistic loan records")
    print(f"📁 Output: {output_path}")
    print("\nDistribution:")
    status_counts = {}
    for loan in loans:
        status = loan["current_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    for status, count in sorted(status_counts.items()):
        percentage = (count / len(loans)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
