"""Compatibility shim: re-exports scripts.generate_sample_data for test imports."""

from scripts.generate_sample_data import (
    Loan,
    generate_loan,
    generate_mexican_rfc,
)

__all__ = ["generate_mexican_rfc", "generate_loan", "Loan"]
