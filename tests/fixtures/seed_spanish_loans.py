from __future__ import annotations
from secrets import choice as secrets_choice
DNI_LETTERS = 'TRWAGMYFPDXBNJZSQVHLCKE'
DIGITS = '0123456789'

def _compute_dni_letter(number: int) -> str:
    return DNI_LETTERS[number % 23]

def generate_dni() -> str:
    number_str = ''.join((secrets_choice(DIGITS) for _ in range(8)))
    number = int(number_str)
    letter = _compute_dni_letter(number)
    return f'{number_str}{letter}'

def generate_nie() -> str:
    initial = secrets_choice('XYZ')
    numeric_body = ''.join((secrets_choice(DIGITS) for _ in range(7)))
    prefix_map = {'X': '0', 'Y': '1', 'Z': '2'}
    transformed = int(prefix_map[initial] + numeric_body)
    control_letter = _compute_dni_letter(transformed)
    return f'{initial}{numeric_body}{control_letter}'
