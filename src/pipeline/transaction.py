from __future__ import annotations

import string
from typing import TypedDict

# IBAN Validation constants
ALPHA = {c: str(ord(c) % 55) for c in string.ascii_uppercase}


class AccountRouting(TypedDict):
    address: str  # IBAN or account number
    routing_number: str


class Account(TypedDict):
    account_routing: AccountRouting
    account_id: str
    owner_name: str


class Transaction(TypedDict):
    this_account: Account
    amount: float
    currency: str
    transaction_date: str


class ProcessedTransaction(Transaction):
    iban_valid: bool
    risk_score: float


def check_iban(iban: str) -> bool:
    """Validates International Bank Account Number (IBAN) using Mod-97."""
    if not isinstance(iban, str):
        return False

    iban_clean = iban.replace(" ", "").upper()
    if len(iban_clean) < 15:
        return False

    rearranged = iban_clean[4:] + iban_clean[:4]

    # Convert letters to numbers
    numeric = "".join(ALPHA.get(c, c) for c in rearranged)

    # Perform mod-97 check
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def process_transaction(data: Transaction) -> ProcessedTransaction:
    raw_iban = data["this_account"]["account_routing"]["address"]
    is_valid = check_iban(raw_iban)

    output: ProcessedTransaction = {
        "this_account": data["this_account"],
        "amount": data["amount"],
        "currency": data["currency"],
        "transaction_date": data["transaction_date"],
        "iban_valid": is_valid,
        "risk_score": 0.0 if is_valid else 1.0,
    }
    return output
