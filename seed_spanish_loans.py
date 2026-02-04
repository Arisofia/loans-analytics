"""Compatibility shim: re-exports scripts.seed_spanish_loans for test imports."""

from scripts.seed_spanish_loans import (
    generate_dni,
    generate_nie,
)

__all__ = ["generate_dni", "generate_nie"]
