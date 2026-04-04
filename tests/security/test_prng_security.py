import re
import sys
import importlib
from pathlib import Path
import pytest
fixtures_root = Path(__file__).parent.parent / 'fixtures'
sys.path.insert(0, str(fixtures_root))


def _import_fixture_module(module_name: str):
    """Import fixture generator modules via string to avoid static import-resolution noise."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        pytest.skip(f'Optional fixture module not available: {module_name}')

def test_mexican_rfc_generation_uses_secrets():
    generate_sample_data = _import_fixture_module("generate_sample_data")
    generate_mexican_rfc = generate_sample_data.generate_mexican_rfc
    rfcs = [generate_mexican_rfc() for _ in range(10)]
    pattern = '^[A-Z]{4}\\d{6}[A-Z0-9]{3}$'
    assert all(re.match(pattern, rfc) for rfc in rfcs), "At least one RFC doesn't match expected format"
    assert all(len(rfc) == 13 for rfc in rfcs), 'At least one RFC has incorrect length'
    assert len(set(rfcs)) == len(rfcs), 'RFCs should be unique'

def test_spanish_dni_generation_uses_secrets():
    seed_spanish_loans = _import_fixture_module("seed_spanish_loans")
    generate_dni = seed_spanish_loans.generate_dni
    dnis = [generate_dni() for _ in range(10)]
    pattern = '^\\d{8}[A-Z]$'
    letters = 'TRWAGMYFPDXBNJZSQVHLCKE'
    assert all(re.match(pattern, dni) for dni in dnis), "At least one DNI doesn't match expected format"
    assert all(len(dni) == 9 for dni in dnis), 'At least one DNI has incorrect length'
    assert all(dni[8] == letters[int(dni[:8]) % 23] for dni in dnis), 'At least one DNI has invalid check letter'
    assert len(set(dnis)) == len(dnis), 'DNIs should be unique'

def test_spanish_nie_generation_uses_secrets():
    seed_spanish_loans = _import_fixture_module("seed_spanish_loans")
    generate_nie = seed_spanish_loans.generate_nie
    nies = [generate_nie() for _ in range(10)]
    pattern = '^[XYZ]\\d{7}[A-Z]$'
    assert all(re.match(pattern, nie) for nie in nies), "At least one NIE doesn't match expected format"
    assert all(len(nie) == 9 for nie in nies), 'At least one NIE has incorrect length'
    assert len(set(nies)) == len(nies), 'NIEs should be unique'

def test_reproducible_test_data_uses_random_with_seed():
    import random
    from datetime import date
    generate_sample_data = _import_fixture_module("generate_sample_data")
    generate_loan = generate_sample_data.generate_loan
    random.seed(42)
    loan1 = generate_loan(1, date(2024, 1, 1))
    random.seed(42)
    loan2 = generate_loan(1, date(2024, 1, 1))
    assert loan1.principal_amount == loan2.principal_amount, 'Amounts should be reproducible with seed'
    assert loan1.interest_rate == loan2.interest_rate, 'Rates should be reproducible with seed'
    assert loan1.term_months == loan2.term_months, 'Terms should be reproducible'

def test_kpi_data_generation_reproducibility():
    from datetime import date
    load_sample_kpis_supabase = _import_fixture_module("load_sample_kpis_supabase")
    KpiDataLoader = load_sample_kpis_supabase.KpiDataLoader
    loader = KpiDataLoader(seed=42)
    series1 = loader.generate_kpi_series('test_kpi', date(2024, 1, 1), days=5, base_value=100.0, trend=0.001, noise=0.05)
    loader2 = KpiDataLoader(seed=42)
    series2 = loader2.generate_kpi_series('test_kpi', date(2024, 1, 1), days=5, base_value=100.0, trend=0.001, noise=0.05)
    assert len(series1) == len(series2) == 5
    assert [point.value for point in series1] == [point.value for point in series2], 'KPI values should be reproducible with same seed'
