import pytest
import re
from src.utils.validation import validate_iban, is_valid_iban

def test_is_valid_iban_fallback_logic():
    # Spanish IBAN
    assert is_valid_iban("ES1234567890123456789012") is True
    # Too short
    assert is_valid_iban("ES123") is False
    # Too long
    assert is_valid_iban("ES" + "1" * 35) is False
    # Basic alphanumeric check
    assert is_valid_iban("DE123456789012345") is True
    assert is_valid_iban("DE!!!!56789012345") is False

def test_validate_iban_edge_cases():
    assert validate_iban(None) is False
    assert validate_iban("") is False
    assert validate_iban("   ") is False
    # Valid with spaces
    assert validate_iban("ES 1234 5678 9012 3456 7890 12") is True
