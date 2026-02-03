"""Compatibility shim: re-exports scripts.generate_sample_data for test imports."""
from scripts.generate_sample_data import (
    generate_mexican_rfc,
    generate_loan,
    Loan,
)  # noqa: F401
