from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Union
logger = logging.getLogger(__name__)
CENTS_PER_DOLLAR = 100
MAX_LOAN_AMOUNT_CENTS = 10000000000
MIN_LOAN_AMOUNT_CENTS = 1
INTEREST_RATE_SCALE = 10000
MAX_INTEREST_RATE = 10000 * 200
ROUNDING_MODE = ROUND_HALF_UP

def dollars_to_cents(amount_dollars: Union[float, str, Decimal]) -> int:
    if isinstance(amount_dollars, float):
        decimal_amount = Decimal(str(amount_dollars))
    elif isinstance(amount_dollars, str):
        decimal_amount = Decimal(amount_dollars)
    else:
        decimal_amount = amount_dollars
    if decimal_amount % Decimal('0.01') != 0:
        raise ValueError(f'Monetary value has more than 2 decimal places: {amount_dollars}. Values must round to nearest cent.')
    cents = int((decimal_amount * Decimal(CENTS_PER_DOLLAR)).quantize(Decimal('1'), rounding=ROUNDING_MODE))
    if cents < MIN_LOAN_AMOUNT_CENTS:
        raise ValueError(f'Loan amount {amount_dollars} is below minimum ($0.01)')
    if cents > MAX_LOAN_AMOUNT_CENTS:
        raise ValueError(f'Loan amount {amount_dollars} exceeds maximum ($100,000,000)')
    return cents

def cents_to_dollars(amount_cents: int) -> Decimal:
    return Decimal(amount_cents) / Decimal(CENTS_PER_DOLLAR)

def interest_rate_to_basis_points(rate_decimal: Union[float, Decimal]) -> int:
    if isinstance(rate_decimal, float):
        decimal_rate = Decimal(str(rate_decimal))
    else:
        decimal_rate = rate_decimal
    basis_points = int((decimal_rate * Decimal(INTEREST_RATE_SCALE)).quantize(Decimal('1'), rounding=ROUNDING_MODE))
    if basis_points < 0:
        raise ValueError(f'Interest rate cannot be negative: {rate_decimal}')
    if basis_points > MAX_INTEREST_RATE:
        raise ValueError(f'Interest rate exceeds maximum (2000%): {rate_decimal}')
    return basis_points

def basis_points_to_interest_rate(basis_points: int) -> Decimal:
    return Decimal(basis_points) / Decimal(INTEREST_RATE_SCALE)

def safe_decimal_sum(values) -> Decimal:
    total = Decimal('0')
    for value in values:
        if isinstance(value, float):
            total += Decimal(str(value))
        else:
            total += Decimal(value)
    return total

def safe_decimal_divide(numerator: Union[int, Decimal], denominator: Union[int, Decimal], precision: int=4) -> Decimal:
    if denominator == 0:
        raise ValueError('Cannot divide by zero')
    numerator_dec = numerator if isinstance(numerator, Decimal) else Decimal(numerator)
    denominator_dec = denominator if isinstance(denominator, Decimal) else denominator
    quantize_exp = Decimal(10) ** (-precision)
    return (numerator_dec / denominator_dec).quantize(quantize_exp, rounding=ROUNDING_MODE)

def validate_monetary_field(field_name: str, value: Union[float, int, str, Decimal]) -> int:
    try:
        cents = dollars_to_cents(value)
        if cents < 100:
            logger.warning(f'{field_name}: Very small amount $0.{cents:02d}')
        if cents > 1000000000:
            logger.warning(f'{field_name}: Large amount exceeds $10M')
        return cents
    except ValueError as e:
        logger.error(f'Validation failed for {field_name}: {e}')
        raise
if __name__ == '__main__':
    print('Testing financial precision module...')
    test_amounts = [10.5, 100.01, 1.99, 0.01]
    for amount in test_amounts:
        cents = dollars_to_cents(amount)
        back = cents_to_dollars(cents)
        print(f'  {amount:.2f} → {cents} cents → {back}')
        assert float(back) == amount, f'Round-trip failed for {amount}'
    test_rates = [0.05, 0.0525, 0.15, 0.25]
    for rate in test_rates:
        bp = interest_rate_to_basis_points(rate)
        back = basis_points_to_interest_rate(bp)
        print(f'  {rate:.4f} → {bp} bp → {back}')
    print('✅ All tests passed!')
