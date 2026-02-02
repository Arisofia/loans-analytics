#!/usr/bin/env python3
"""
Seed script for generating realistic Spanish loan records.

Generates 800+ realistic loan records with:
- Spanish names and surnames
- Valid DNI/NIE numbers
- Spanish regions (Comunidades Autónomas)
- Realistic loan amounts, rates, terms
- Varied statuses: current, delinquent, paid-off, default
- Payment history with delays and defaults
- Risk scores based on loan performance
"""

import csv
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Spanish names and surnames (common in Spain)
SPANISH_FIRST_NAMES = [
    # Male names
    "Antonio",
    "José",
    "Manuel",
    "Francisco",
    "David",
    "Juan",
    "Javier",
    "Daniel",
    "Carlos",
    "Miguel",
    "Alejandro",
    "Pedro",
    "Jesús",
    "Rafael",
    "Pablo",
    "Sergio",
    "Fernando",
    "Ángel",
    "Luis",
    "Jorge",
    "Alberto",
    "Raúl",
    "Roberto",
    "Andrés",
    # Female names
    "María",
    "Carmen",
    "Dolores",
    "Isabel",
    "Ana",
    "Josefa",
    "Francisca",
    "Pilar",
    "Teresa",
    "Rosa",
    "Antonia",
    "Lucía",
    "Marta",
    "Elena",
    "Laura",
    "Sara",
    "Cristina",
    "Patricia",
    "Beatriz",
    "Natalia",
    "Silvia",
    "Raquel",
    "Mónica",
    "Eva",
]

SPANISH_SURNAMES = [
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
    "Álvarez",
    "Muñoz",
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
    "Molina",
    "Castro",
    "Ortega",
    "Delgado",
    "Ortiz",
    "Morales",
    "Iglesias",
    "Santos",
    "Guerrero",
    "Medina",
    "Garrido",
    "Cortés",
    "Castillo",
    "Rubio",
    "Moya",
    "Pardo",
]

# Spanish regions (Comunidades Autónomas)
SPANISH_REGIONS = [
    "Andalucía",
    "Aragón",
    "Asturias",
    "Baleares",
    "Canarias",
    "Cantabria",
    "Castilla y León",
    "Castilla-La Mancha",
    "Cataluña",
    "Comunidad Valenciana",
    "Extremadura",
    "Galicia",
    "Madrid",
    "Murcia",
    "Navarra",
    "País Vasco",
    "La Rioja",
]

# Loan statuses with realistic distribution
LOAN_STATUSES = {
    "current": 0.65,  # 65% current/performing
    "delinquent": 0.20,  # 20% delinquent (various DPD)
    "paid-off": 0.10,  # 10% paid off
    "default": 0.05,  # 5% defaulted
}


def generate_dni() -> str:
    """Generate a valid Spanish DNI (Documento Nacional de Identidad)."""
    # DNI format: 8 digits + letter
    number = random.randint(10000000, 99999999)
    letters = "TRWAGMYFPDXBNJZSQVHLCKE"
    letter = letters[number % 23]
    return f"{number:08d}{letter}"


def generate_nie() -> str:
    """Generate a valid Spanish NIE (Número de Identificación de Extranjero)."""
    # NIE format: X/Y/Z + 7 digits + letter
    prefix = random.choice(["X", "Y", "Z"])
    number = random.randint(1000000, 9999999)

    # Calculate check letter
    nie_number = number
    if prefix == "X":
        nie_number = number
    elif prefix == "Y":
        nie_number = 10000000 + number
    elif prefix == "Z":
        nie_number = 20000000 + number

    letters = "TRWAGMYFPDXBNJZSQVHLCKE"
    letter = letters[nie_number % 23]
    return f"{prefix}{number:07d}{letter}"


def generate_id_number() -> str:
    """Generate either DNI or NIE (80% DNI, 20% NIE)."""
    if random.random() < 0.8:
        return generate_dni()
    else:
        return generate_nie()


def generate_email(name: str, surname: str) -> str:
    """Generate realistic Spanish email."""
    domains = ["gmail.com", "hotmail.com", "yahoo.es", "outlook.es", "icloud.com"]
    # Remove accents for email
    name_clean = (
        name.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    surname_clean = (
        surname.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )

    patterns = [
        f"{name_clean}.{surname_clean}@{random.choice(domains)}",
        f"{name_clean}{surname_clean}@{random.choice(domains)}",
        f"{name_clean[0]}{surname_clean}@{random.choice(domains)}",
        f"{name_clean}_{random.randint(1, 999)}@{random.choice(domains)}",
    ]
    return random.choice(patterns)


def generate_payment_history(
    status: str, term_months: int, origination_date: datetime, monthly_payment: float
) -> list[dict[str, Any]]:
    """Generate realistic payment history based on loan status."""
    history = []
    current_date = origination_date

    # Determine how many payments should be made
    months_since_origination = (datetime.now() - origination_date).days // 30
    payments_expected = min(months_since_origination, term_months)

    if status == "current":
        # Current loans: mostly on-time payments, occasional small delays
        for i in range(payments_expected):
            current_date = origination_date + timedelta(days=30 * i)
            delay_days = 0

            # 10% chance of small delay
            if random.random() < 0.10:
                delay_days = random.randint(1, 15)

            history.append(
                {
                    "payment_number": i + 1,
                    "due_date": current_date.strftime("%Y-%m-%d"),
                    "paid_date": (current_date + timedelta(days=delay_days)).strftime("%Y-%m-%d"),
                    "amount_due": round(monthly_payment, 2),
                    "amount_paid": round(monthly_payment, 2),
                    "days_late": delay_days,
                    "status": "paid" if delay_days == 0 else "late_paid",
                }
            )

    elif status == "delinquent":
        # Delinquent loans: good history then delays/missed payments
        good_payments = int(payments_expected * 0.6)

        # Good payment history
        for i in range(good_payments):
            current_date = origination_date + timedelta(days=30 * i)
            delay_days = random.randint(0, 5) if random.random() < 0.2 else 0

            history.append(
                {
                    "payment_number": i + 1,
                    "due_date": current_date.strftime("%Y-%m-%d"),
                    "paid_date": (current_date + timedelta(days=delay_days)).strftime("%Y-%m-%d"),
                    "amount_due": round(monthly_payment, 2),
                    "amount_paid": round(monthly_payment, 2),
                    "days_late": delay_days,
                    "status": "paid" if delay_days == 0 else "late_paid",
                }
            )

        # Then increasing delays and missed payments
        for i in range(good_payments, payments_expected):
            current_date = origination_date + timedelta(days=30 * i)

            if random.random() < 0.4:
                # Missed payment
                history.append(
                    {
                        "payment_number": i + 1,
                        "due_date": current_date.strftime("%Y-%m-%d"),
                        "paid_date": None,
                        "amount_due": round(monthly_payment, 2),
                        "amount_paid": 0,
                        "days_late": (datetime.now() - current_date).days,
                        "status": "missed",
                    }
                )
            else:
                # Late payment
                delay_days = random.randint(30, 90)
                history.append(
                    {
                        "payment_number": i + 1,
                        "due_date": current_date.strftime("%Y-%m-%d"),
                        "paid_date": (current_date + timedelta(days=delay_days)).strftime(
                            "%Y-%m-%d"
                        ),
                        "amount_due": round(monthly_payment, 2),
                        "amount_paid": round(monthly_payment * random.uniform(0.5, 1.0), 2),
                        "days_late": delay_days,
                        "status": "late_paid",
                    }
                )

    elif status == "paid-off":
        # Paid off loans: complete payment history
        for i in range(term_months):
            current_date = origination_date + timedelta(days=30 * i)
            delay_days = random.randint(0, 7) if random.random() < 0.15 else 0

            history.append(
                {
                    "payment_number": i + 1,
                    "due_date": current_date.strftime("%Y-%m-%d"),
                    "paid_date": (current_date + timedelta(days=delay_days)).strftime("%Y-%m-%d"),
                    "amount_due": round(monthly_payment, 2),
                    "amount_paid": round(monthly_payment, 2),
                    "days_late": delay_days,
                    "status": "paid",
                }
            )

    elif status == "default":
        # Defaulted loans: some payments then stopped
        payments_made = int(payments_expected * random.uniform(0.2, 0.5))

        for i in range(payments_made):
            current_date = origination_date + timedelta(days=30 * i)
            delay_days = random.randint(0, 30) if random.random() < 0.5 else 0

            history.append(
                {
                    "payment_number": i + 1,
                    "due_date": current_date.strftime("%Y-%m-%d"),
                    "paid_date": (
                        (current_date + timedelta(days=delay_days)).strftime("%Y-%m-%d")
                        if delay_days < 180
                        else None
                    ),
                    "amount_due": round(monthly_payment, 2),
                    "amount_paid": (
                        round(monthly_payment * random.uniform(0.3, 1.0), 2)
                        if delay_days < 180
                        else 0
                    ),
                    "days_late": delay_days,
                    "status": (
                        "paid"
                        if delay_days < 30
                        else "late_paid" if delay_days < 180 else "defaulted"
                    ),
                }
            )

        # Rest are missed
        for i in range(payments_made, payments_expected):
            current_date = origination_date + timedelta(days=30 * i)
            history.append(
                {
                    "payment_number": i + 1,
                    "due_date": current_date.strftime("%Y-%m-%d"),
                    "paid_date": None,
                    "amount_due": round(monthly_payment, 2),
                    "amount_paid": 0,
                    "days_late": (datetime.now() - current_date).days,
                    "status": "defaulted",
                }
            )

    return history


def calculate_risk_score(
    status: str,
    payment_history: list[dict[str, Any]],
    principal_amount: float,
    interest_rate: float,
) -> float:
    """Calculate risk score based on loan characteristics and payment history."""
    base_score = 0.5

    # Status adjustment
    status_scores = {"current": 0.2, "delinquent": 0.6, "paid-off": 0.1, "default": 0.95}
    base_score = status_scores.get(status, 0.5)

    # Payment history adjustment
    if payment_history:
        total_payments = len(payment_history)
        late_payments = sum(1 for p in payment_history if p["days_late"] > 0)
        missed_payments = sum(1 for p in payment_history if p["status"] in ["missed", "defaulted"])

        if total_payments > 0:
            late_ratio = late_payments / total_payments
            missed_ratio = missed_payments / total_payments
            base_score += late_ratio * 0.2 + missed_ratio * 0.3

    # Amount and rate adjustment
    if principal_amount > 50000:
        base_score += 0.05
    if interest_rate > 0.15:
        base_score += 0.05

    # Cap between 0 and 1
    return min(max(base_score, 0.0), 1.0)


def generate_loan_record(loan_id: int) -> dict[str, Any]:
    """Generate a single realistic loan record."""
    # Basic borrower info
    first_name = random.choice(SPANISH_FIRST_NAMES)
    surname1 = random.choice(SPANISH_SURNAMES)
    surname2 = random.choice(SPANISH_SURNAMES)
    borrower_name = f"{first_name} {surname1} {surname2}"
    borrower_id_number = generate_id_number()
    borrower_email = generate_email(first_name, surname1)

    # Loan characteristics
    # Status distribution according to realistic portfolio
    rand = random.random()
    cumulative = 0
    status = "current"
    for s, prob in LOAN_STATUSES.items():
        cumulative += prob
        if rand <= cumulative:
            status = s
            break

    # Principal amount: €5,000 to €100,000
    principal_amount = round(random.uniform(5000, 100000), 2)

    # Interest rate: 5% to 20% annual
    interest_rate = round(random.uniform(0.05, 0.20), 4)

    # Term: 12, 24, 36, 48, or 60 months
    term_months = random.choice([12, 24, 36, 48, 60])

    # Origination date: between 3 years ago and 6 months ago
    days_ago = random.randint(180, 1095)
    origination_date = datetime.now() - timedelta(days=days_ago)

    # Calculate monthly payment (simple amortization)
    monthly_rate = interest_rate / 12
    if monthly_rate > 0:
        monthly_payment = (
            principal_amount
            * (monthly_rate * (1 + monthly_rate) ** term_months)
            / ((1 + monthly_rate) ** term_months - 1)
        )
    else:
        monthly_payment = principal_amount / term_months

    # Generate payment history
    payment_history = generate_payment_history(
        status, term_months, origination_date, monthly_payment
    )

    # Calculate risk score
    risk_score = calculate_risk_score(status, payment_history, principal_amount, interest_rate)

    # Region
    region = random.choice(SPANISH_REGIONS)

    return {
        "loan_id": f"ES-{loan_id:06d}",
        "borrower_name": borrower_name,
        "borrower_email": borrower_email,
        "borrower_id_number": borrower_id_number,
        "principal_amount": principal_amount,
        "interest_rate": interest_rate,
        "term_months": term_months,
        "origination_date": origination_date.strftime("%Y-%m-%d"),
        "current_status": status,
        "payment_history_json": json.dumps(payment_history, ensure_ascii=False),
        "risk_score": round(risk_score, 4),
        "region": region,
    }


def generate_loan_dataset(num_records: int = 800) -> list[dict[str, Any]]:
    """Generate complete dataset of Spanish loan records."""
    print(f"Generating {num_records} realistic Spanish loan records...")

    records = []
    for i in range(1, num_records + 1):
        if i % 100 == 0:
            print(f"  Generated {i}/{num_records} records...")
        records.append(generate_loan_record(i))

    # Calculate summary statistics
    status_counts = {}
    region_counts = {}
    principals = []
    rates = []
    risks = []

    for r in records:
        status_counts[r["current_status"]] = status_counts.get(r["current_status"], 0) + 1
        region_counts[r["region"]] = region_counts.get(r["region"], 0) + 1
        principals.append(r["principal_amount"])
        rates.append(r["interest_rate"])
        risks.append(r["risk_score"])

    # Print summary statistics
    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(records)}")
    print(f"\nStatus distribution:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    print(f"\nTop 5 regions:")
    for region, count in sorted(region_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {region}: {count}")
    print(f"\nPrincipal amount statistics:")
    print(f"  Mean: €{sum(principals)/len(principals):,.2f}")
    print(f"  Min: €{min(principals):,.2f}")
    print(f"  Max: €{max(principals):,.2f}")
    print(f"\nInterest rate statistics:")
    print(f"  Mean: {sum(rates)/len(rates):.2%}")
    print(f"  Min: {min(rates):.2%}")
    print(f"  Max: {max(rates):.2%}")
    print(f"\nRisk score statistics:")
    print(f"  Mean: {sum(risks)/len(risks):.4f}")
    print(f"  Min: {min(risks):.4f}")
    print(f"  Max: {max(risks):.4f}")
    print("=" * 60)

    return records


def main():
    """Main function to generate and save loan dataset."""
    # Set random seed for reproducibility
    random.seed(42)

    # Generate dataset
    records = generate_loan_dataset(
        num_records=850
    )  # Generate 850 to have 800+ after any filtering

    # Save to CSV
    output_dir = Path(__file__).parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get fieldnames from first record
    fieldnames = list(records[0].keys())

    # Save full dataset
    output_file = output_dir / "spanish_loans_seed.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n✅ Dataset saved to: {output_file}")
    print(f"✅ Ready to upload or process through pipeline")

    # Also save a sample for quick testing
    sample_file = output_dir / "spanish_loans_sample.csv"
    with open(sample_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records[:50])

    print(f"✅ Sample (50 records) saved to: {sample_file}")


if __name__ == "__main__":
    main()
