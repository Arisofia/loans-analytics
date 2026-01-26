#!/usr/bin/env python3
"""Simple, typed data processor for transactions (demo).

Implements TypedDict schemas and IBAN validation (mod-97).
"""
from __future__ import annotations

import string
from typing import TypedDict

# --- Robust TypedDict Schema ---

class AccountRouting(TypedDict):
    address: str
    routing_number: str


class Account(TypedDict):
    account_routing: AccountRouting
    account_id: str
    owner_name: str


class Transaction(TypedDict):
    this_account: Account
    amount: float
    currency: str


# --- IBAN Logic ---
ALPHA = {c: str(ord(c) % 55) for c in string.ascii_uppercase}


def validate_iban(iban: str) -> bool:
    iban = iban.replace(" ", "").upper()
    if len(iban) < 15:
        return False
    rearranged = iban[4:] + iban[:4]

    try:
        numeric = ''.join(ALPHA.get(c, c) for c in rearranged)
        return int(numeric) % 97 == 1
    except ValueError:
        return False


# --- Main Processor ---

def run_pipeline(data: Transaction) -> None:
    iban = data['this_account']['account_routing']['address']
    validate_iban(iban)
    print(f"Processed transaction of amount ${data['amount']}")


if __name__ == "__main__":
    # Example Mock Data
    mock_tx: Transaction = {
        'this_account': {
            'account_routing': {'address': 'DE89370400440532013000', 'routing_number': 'GEN'},
            'account_id': '123',
            'owner_name': 'Test Corp'
        },
        'amount': 1000.50,
        'currency': 'EUR'
    }
    run_pipeline(mock_tx)
