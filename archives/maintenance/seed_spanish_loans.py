"""
Spanish national identifier generators for synthetic test data.

Security: Uses `secrets` for all ID generation to ensure unpredictability
and avoid accidental collision with real identifiers.

Follows python:S2245 guidelines for PRNG usage in security contexts.
"""

from __future__ import annotations

from secrets import choice as secrets_choice

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
DIGITS = "0123456789"


def _compute_dni_letter(number: int) -> str:
    """Compute the control letter for a DNI/NIE."""
    return DNI_LETTERS[number % 23]


def generate_dni() -> str:
    """
    Generate synthetic Spanish DNI (Documento Nacional de Identidad).

    Security: Uses `secrets` for the numeric body so IDs are non-predictable
    and non-reproducible, avoiding accidental collision with real identifiers.

    Format: 8 digits + control letter
    """
    number_str = "".join(secrets_choice(DIGITS) for _ in range(8))
    number = int(number_str)
    letter = _compute_dni_letter(number)
    return f"{number_str}{letter}"


def generate_nie() -> str:
    """
    Generate synthetic Spanish NIE (Número de Identidad de Extranjero).

    Security: Uses `secrets` and standard NIE structure:
    - Initial letter: X/Y/Z
    - 7 digits
    - Control letter derived from transformed number

    Avoids accidental collision with real foreign identifiers.
    """
    initial = secrets_choice("XYZ")
    numeric_body = "".join(secrets_choice(DIGITS) for _ in range(7))

    # Standard transformation: replace X/Y/Z with 0/1/2 and compute DNI letter
    prefix_map = {"X": "0", "Y": "1", "Z": "2"}
    transformed = int(prefix_map[initial] + numeric_body)
    control_letter = _compute_dni_letter(transformed)
    return f"{initial}{numeric_body}{control_letter}"
