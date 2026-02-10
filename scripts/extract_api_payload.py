#!/usr/bin/env python3
"""Extract real loan records from CSV for API testing.

Maps CSV columns to the LoanRecord Pydantic model:
  loan_amount     <- principal_amount
  appraised_value <- collateral_value (or principal*1.2 if missing)
  borrower_income <- tpv*12 (factoring: annual revenue proxy)
  monthly_debt    <- outstanding_balance / term_months
  loan_status     <- current_status (mapped to API enum)
  interest_rate   <- interest_rate
  principal_balance <- outstanding_balance
"""

import csv
import json
from pathlib import Path

CSV_PATH = Path("data/raw/abaco_real_data_20260202.csv")
OUT_PATH = Path("data/output/abaco_api_payload.json")

STATUS_MAP = {
    "Current": "current",
    "Pagado": "current",
    "Vencido": "90+ days past due",
    "En Mora": "30-59 days past due",
    "Castigado": "90+ days past due",
}


def safe_float(val, default=0.0):
    """Safely convert a value to float, returning *default* on failure."""
    try:
        return float(val) if val else default
    except (ValueError, TypeError):
        return default


loans = []
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 20:
            break
        try:
            principal = safe_float(row.get("principal_amount"))
            outstanding = safe_float(row.get("outstanding_balance"))
            collateral = safe_float(row.get("collateral_value"))
            tpv = safe_float(row.get("tpv"))
            term = max(int(safe_float(row.get("term_months"), 12)), 1)
            raw_status = (row.get("current_status") or "Unknown").strip()

            loans.append(
                {
                    "id": row.get("loan_id", f"LOAN_{i}"),
                    "loan_amount": principal if principal > 0 else outstanding,
                    "appraised_value": collateral if collateral > 0 else principal * 1.2,
                    "borrower_income": tpv * 12 if tpv > 0 else principal * 3,
                    "monthly_debt": outstanding / term,
                    "loan_status": STATUS_MAP.get(raw_status, "current"),
                    "interest_rate": safe_float(row.get("interest_rate")),
                    "principal_balance": outstanding if outstanding > 0 else principal,
                }
            )
        except (ValueError, TypeError):
            pass

payload = {"loans": loans}
with open(OUT_PATH, "w") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote {len(payload['loans'])} loans to {OUT_PATH}")
print(json.dumps(payload["loans"][0], indent=2))
