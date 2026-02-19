"""
Seed historical_kpis table with 120 days of realistic daily KPI data.

Generates data from Oct 10 2025 through Feb 7 2026, producing realistic
trends, weekly cycles, and noise for all 19 pipeline KPIs plus 4
multi-agent KPIs (npl_ratio, approval_rate, cost_of_risk, conversion_rate).

Usage:
    cd project_root
    set -a && source .env.local && set +a
    python scripts/seed_historical_kpis.py
"""

import math
import os
import random
import sys
from datetime import date, timedelta
from typing import Any, Dict, List

import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_SECRET_API_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not API_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SECRET_API_KEY must be set")
    sys.exit(1)

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

TABLE_URL = f"{SUPABASE_URL}/rest/v1/historical_kpis"

# Seed for reproducibility
random.seed(42)

# Date range: 120 days ending yesterday
END_DATE = date(2026, 2, 7)
START_DATE = END_DATE - timedelta(days=119)
DAYS = 120

# KPI definitions: (base_value, daily_noise_pct, trend_per_day, is_count, unit)
# Trends simulate realistic portfolio evolution:
# - PAR30/PAR90: slightly increasing (portfolio aging)
# - Collections: stable with slight improvement
# - Outstanding balance: growing (new disbursements)
# - Yield: stable
KPI_CONFIGS = {
    # Pipeline asset quality KPIs
    "par_30": {
        "base": 5.8,
        "noise": 0.08,
        "trend": 0.005,
        "is_count": False,
        "desc": "Portfolio at Risk 30 days (%)",
    },
    "par_90": {
        "base": 3.5,
        "noise": 0.06,
        "trend": 0.007,
        "is_count": False,
        "desc": "Portfolio at Risk 90 days (%)",
    },
    "default_rate": {
        "base": 1.8,
        "noise": 0.05,
        "trend": 0.003,
        "is_count": False,
        "desc": "Default rate (%)",
    },
    "loss_rate": {
        "base": 2.0,
        "noise": 0.04,
        "trend": 0.003,
        "is_count": False,
        "desc": "Loss rate (%)",
    },
    # Pipeline cash flow KPIs
    "collections_rate": {
        "base": 88.0,
        "noise": 0.03,
        "trend": 0.02,
        "is_count": False,
        "desc": "Collection efficiency (%)",
    },
    "recovery_rate": {
        "base": 55.0,
        "noise": 0.06,
        "trend": 0.04,
        "is_count": False,
        "desc": "Recovery rate on defaulted loans (%)",
    },
    "cash_on_hand": {
        "base": 7500000.0,
        "noise": 0.02,
        "trend": 4500.0,
        "is_count": False,
        "desc": "Total cash position (USD)",
    },
    # Pipeline portfolio KPIs
    "total_outstanding_balance": {
        "base": 7200000.0,
        "noise": 0.015,
        "trend": 7000.0,
        "is_count": False,
        "desc": "Total outstanding balance (USD)",
    },
    "total_loans_count": {
        "base": 1050,
        "noise": 0.01,
        "trend": 1.2,
        "is_count": True,
        "desc": "Active loans count",
    },
    "average_loan_size": {
        "base": 3150.0,
        "noise": 0.02,
        "trend": 1.2,
        "is_count": False,
        "desc": "Average loan size (USD)",
    },
    "portfolio_yield": {
        "base": 62.0,
        "noise": 0.02,
        "trend": 0.02,
        "is_count": False,
        "desc": "Average interest rate (%)",
    },
    # Pipeline customer KPIs
    "active_borrowers": {
        "base": 120,
        "noise": 0.02,
        "trend": 0.17,
        "is_count": True,
        "desc": "Active borrowers count",
    },
    "repeat_borrower_rate": {
        "base": 95.0,
        "noise": 0.01,
        "trend": 0.04,
        "is_count": False,
        "desc": "Repeat borrower rate (%)",
    },
    "customer_lifetime_value": {
        "base": 180000.0,
        "noise": 0.02,
        "trend": 100.0,
        "is_count": False,
        "desc": "CLV (USD)",
    },
    # Pipeline operational KPIs
    "processing_time_avg": {
        "base": 1.5,
        "noise": 0.03,
        "trend": -0.002,
        "is_count": False,
        "desc": "Average loan term (months)",
    },
    "automation_rate": {
        "base": 98.0,
        "noise": 0.005,
        "trend": 0.015,
        "is_count": False,
        "desc": "Automation rate (%)",
    },
    # Pipeline growth KPIs
    "disbursement_volume_mtd": {
        "base": 450000.0,
        "noise": 0.10,
        "trend": 2000.0,
        "is_count": False,
        "desc": "Monthly disbursement volume (USD)",
    },
    "new_loans_count_mtd": {
        "base": 80,
        "noise": 0.08,
        "trend": 0.3,
        "is_count": True,
        "desc": "New loans this month",
    },
    "portfolio_growth_rate": {
        "base": 3.5,
        "noise": 0.15,
        "trend": 0.01,
        "is_count": False,
        "desc": "MoM portfolio growth (%)",
    },
    # Multi-agent specific KPIs (used by summarize_kpis_real_mode.py)
    "npl_ratio": {
        "base": 0.042,
        "noise": 0.06,
        "trend": 0.00005,
        "is_count": False,
        "desc": "Non-performing loan ratio (decimal)",
    },
    "approval_rate": {
        "base": 0.72,
        "noise": 0.03,
        "trend": 0.0003,
        "is_count": False,
        "desc": "Loan approval rate (decimal)",
    },
    "cost_of_risk": {
        "base": 0.018,
        "noise": 0.05,
        "trend": 0.00002,
        "is_count": False,
        "desc": "Cost of risk (decimal)",
    },
    "conversion_rate": {
        "base": 0.35,
        "noise": 0.04,
        "trend": 0.0004,
        "is_count": False,
        "desc": "Application to disbursement conversion (decimal)",
    },
}


def generate_kpi_value(config: Dict[str, Any], day_offset: int) -> float:
    """Generate a realistic KPI value for a given day offset."""
    base = config["base"]
    noise_pct = config["noise"]
    trend = config["trend"]
    is_count = config["is_count"]

    # Linear trend
    value = base + trend * day_offset

    # Weekly seasonality (lower on weekends)
    weekday = (START_DATE + timedelta(days=day_offset)).weekday()
    if weekday >= 5:  # Sat/Sun
        seasonal = -0.02 if not is_count else -0.05
    else:
        seasonal = 0.005 * math.sin(2 * math.pi * weekday / 5)
    value *= 1 + seasonal

    # Random noise (Gaussian)
    noise = random.gauss(0, noise_pct)
    value *= 1 + noise

    # Ensure non-negative
    value = max(0.0, value)

    if is_count:
        value = round(value)

    return value


def generate_all_records() -> List[Dict[str, Any]]:
    """Generate all KPI records for the full date range."""
    records = []
    run_id = "seed_historical_120d"

    for day_offset in range(DAYS):
        current_date = START_DATE + timedelta(days=day_offset)
        date_str = current_date.isoformat()

        for kpi_id, config in KPI_CONFIGS.items():
            value = generate_kpi_value(config, day_offset)

            record = {
                "kpi_id": kpi_id,
                "date": date_str,
                "value_numeric": round(value, 6),
                "value_int": int(value) if config["is_count"] else None,
                "source_system": "historical_seed",
                "run_id": run_id,
                "is_final": True,
            }

            records.append(record)

    return records


def insert_batch(records: List[Dict[str, Any]]) -> int:
    """Insert a batch of records into Supabase. Returns count inserted."""
    response = requests.post(
        TABLE_URL,
        headers=HEADERS,
        json=records,
        timeout=60,
    )
    if not response.ok:
        print(f"    HTTP {response.status_code}: {response.text[:500]}")
    response.raise_for_status()
    return len(records)


def main():
    print(f"Generating {DAYS} days of historical KPI data...")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"KPIs: {len(KPI_CONFIGS)}")

    records = generate_all_records()
    total = len(records)
    print(f"Total records to insert: {total}")

    # Insert in batches of 100 (Supabase payload limit)
    BATCH_SIZE = 100
    inserted = 0

    for i in range(0, total, BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        try:
            count = insert_batch(batch)
            inserted += count
            print(f"  Batch {i // BATCH_SIZE + 1}: {count} recs (total: {inserted}/{total})")
        except requests.HTTPError as e:
            print(f"  ERROR inserting batch {i // BATCH_SIZE + 1}: {e}")
            print(f"  Response: {e.response.text if e.response else 'N/A'}")
            sys.exit(1)

    print(f"\nDone! Inserted {inserted} records into historical_kpis")
    print(f"  {len(KPI_CONFIGS)} KPIs x {DAYS} days = {total} records")

    # Verify
    verify_url = f"{TABLE_URL}?select=kpi_id,date&order=date.desc&limit=5"
    resp = requests.get(
        verify_url,
        headers={
            "apikey": API_KEY,
            "Authorization": f"Bearer {API_KEY}",
        },
        timeout=10,
    )
    if resp.ok:
        print("\nVerification (latest 5 records):")
        for row in resp.json():
            print(f"  {row['kpi_id']}: {row['date']}")


if __name__ == "__main__":
    main()
