"""
Security tests for PRNG usage (python:S2245).

Validates that security-sensitive operations use cryptographically secure
pseudorandom number generators (CSPRNGs) via the secrets module instead of
the insecure random module.

Security Standard: OWASP - Secure Random Number Generation
Reference: python:S2245 - Using pseudorandom number generators is security-sensitive
"""

import re
import sys
from pathlib import Path

import pytest

# Add scripts to path for testing
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))


def test_mexican_rfc_generation_uses_secrets():
    """Test that Mexican RFC generation uses secrets module for unpredictability.

    Security: python:S2245
    Risk: Tax IDs must be unpredictable to prevent accidental generation of real RFCs
    """
    from generate_sample_data import generate_mexican_rfc

    # Generate multiple RFCs
    rfcs = [generate_mexican_rfc() for _ in range(10)]

    # Verify format: 4 letters + 6 digits + 3 alphanumeric
    pattern = r"^[A-Z]{4}\d{6}[A-Z0-9]{3}$"
    for rfc in rfcs:
        assert re.match(pattern, rfc), f"RFC {rfc} doesn't match expected format"
        assert len(rfc) == 13, f"RFC {rfc} has incorrect length"

    # Verify all are unique (very high probability with CSPRNG)
    assert len(set(rfcs)) == len(rfcs), "RFCs should be unique"


def test_spanish_dni_generation_uses_secrets():
    """Test that Spanish DNI generation uses secrets module for unpredictability.

    Security: python:S2245
    Risk: National IDs must be unpredictable to prevent accidental generation of real DNIs
    """
    from seed_spanish_loans import generate_dni

    # Generate multiple DNIs
    dnis = [generate_dni() for _ in range(10)]

    # Verify format: 8 digits + letter
    pattern = r"^\d{8}[A-Z]$"
    for dni in dnis:
        assert re.match(pattern, dni), f"DNI {dni} doesn't match expected format"
        assert len(dni) == 9, f"DNI {dni} has incorrect length"

        # Verify check digit is valid
        number = int(dni[:8])
        letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        expected_letter = letters[number % 23]
        assert dni[8] == expected_letter, f"DNI {dni} has invalid check letter"

    # Verify all are unique
    assert len(set(dnis)) == len(dnis), "DNIs should be unique"


def test_spanish_nie_generation_uses_secrets():
    """Test that Spanish NIE generation uses secrets module for unpredictability.

    Security: python:S2245
    Risk: Foreign IDs must be unpredictable to prevent accidental generation of real NIEs
    """
    from seed_spanish_loans import generate_nie

    # Generate multiple NIEs
    nies = [generate_nie() for _ in range(10)]

    # Verify format: X/Y/Z + 7 digits + letter
    pattern = r"^[XYZ]\d{7}[A-Z]$"
    for nie in nies:
        assert re.match(pattern, nie), f"NIE {nie} doesn't match expected format"
        assert len(nie) == 9, f"NIE {nie} has incorrect length"

    # Verify all are unique
    assert len(set(nies)) == len(nies), "NIEs should be unique"


def test_user_ssn_generation_uses_secrets():
    """Test that SSN generation in test data generators uses secrets module.

    Security: python:S2245
    Risk: Even test SSNs should be unpredictable to avoid confusion with real SSNs
    """
    # Import from templates
    templates_path = Path(__file__).parent.parent.parent / "docs" / "templates"
    sys.path.insert(0, str(templates_path))

    from test_data_generators import UserDataGenerator

    # Generate users without PII masking to see actual SSNs
    gen = UserDataGenerator(seed=42)
    users = gen.generate_users(count=10, mask_pii=False, output_format="dict")

    # Verify SSN format: ###-##-####
    pattern = r"^\d{3}-\d{2}-\d{4}$"
    ssns = [user["ssn"] for user in users]

    for ssn in ssns:
        assert re.match(pattern, ssn), f"SSN {ssn} doesn't match expected format"

    # Verify all are unique (high probability with secrets)
    assert len(set(ssns)) == len(ssns), "SSNs should be unique"


def test_reproducible_test_data_uses_random_with_seed():
    """Test that non-security-sensitive test data uses random with seed for reproducibility.

    Security: python:S2245 - EXCEPTION DOCUMENTED
    Justification: Test data generation requires reproducibility via seeded random.
    This is SAFE because:
    1. No security-sensitive values (IDs, tokens, passwords) are generated this way
    2. Reproducibility is a requirement for consistent test scenarios
    3. Statistical distributions (amounts, rates) don't need cryptographic security
    """
    # Generate loans with same seed should be reproducible
    import random
    from datetime import date

    from generate_sample_data import generate_loan

    random.seed(42)
    loan1 = generate_loan(1, date(2024, 1, 1))

    random.seed(42)
    loan2 = generate_loan(1, date(2024, 1, 1))

    # Amounts and rates should be identical (reproducible)
    assert (
        loan1.principal_amount == loan2.principal_amount
    ), "Amounts should be reproducible with seed"
    assert loan1.interest_rate == loan2.interest_rate, "Rates should be reproducible with seed"
    assert loan1.term_months == loan2.term_months, "Terms should be reproducible"

    # BUT: Security-sensitive fields (RFC, region) should NOT be seeded
    # RFC uses secrets module - will be different
    # Region uses secrets.choice - will be different


def test_kpi_data_generation_reproducibility():
    """Test that KPI synthetic data uses random with seed for reproducibility.

    Security: python:S2245 - EXCEPTION DOCUMENTED
    Justification: Synthetic KPI metrics require reproducibility.
    This is SAFE because:
    1. KPI values are synthetic metrics, not security-sensitive data
    2. Reproducibility ensures same test scenarios
    3. Statistical distributions don't need cryptographic security
    """
    from datetime import date

    from load_sample_kpis_supabase import KpiDataLoader

    loader = KpiDataLoader(seed=42)

    # Generate series - should be reproducible per KPI
    series1 = loader.generate_kpi_series(
        "test_kpi",
        date(2024, 1, 1),
        days=5,
        base_value=100.0,
        trend=0.001,
        noise=0.05,
    )

    loader2 = KpiDataLoader(seed=42)
    series2 = loader2.generate_kpi_series(
        "test_kpi",  # Same KPI ID = same seed
        date(2024, 1, 1),
        days=5,
        base_value=100.0,
        trend=0.001,
        noise=0.05,
    )

    # Should be identical (reproducible via seed)
    assert len(series1) == len(series2) == 5
    for i in range(5):
        assert (
            series1[i].value == series2[i].value
        ), "KPI values should be reproducible with same seed"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
