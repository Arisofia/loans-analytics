from src.pipeline.transaction import check_iban, process_transaction


def test_check_iban_valid_example():
    # Example valid IBAN (DE89 3704 0044 0532 0130 00)
    assert check_iban("DE89 3704 0044 0532 0130 00") is True


def test_check_iban_invalid_example():
    assert check_iban("INVALIDIBAN123") is False


def test_process_transaction_enriches_with_iban():
    txn = {
        "this_account": {
            "account_routing": {"address": "DE89 3704 0044 0532 0130 00", "routing_number": "37040044"},
            "account_id": "acct_1",
            "owner_name": "Alice",
        },
        "amount": 100.0,
        "currency": "EUR",
        "transaction_date": "2025-12-31",
    }
    out = process_transaction(txn)
    assert out["iban_valid"] is True
    assert out["risk_score"] == 0.0
