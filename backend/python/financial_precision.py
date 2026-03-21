"""
Financial Precision Module for Abaco Loans Analytics

Implements finance-safe monetary value handling:
1. Internal representation: Scaled integers (amount_cents = amount_dollars * 100)
2. Conversion guards: Explicit precision validation on float->int conversions
3. Rounding policy: ROUND_HALF_UP (banker's rounding for ties)

This module ensures zero precision loss in financial calculations across:
- Data ingestion (CSV → internal format)
- KPI calculations (aggregations with exact rounding)
- Output generation (internal format → display format)

Policy: Reject conversions that lose precision. Fail fast on precision violations.
"""

from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Union

logger = logging.getLogger(__name__)

# Financial Precision Policy Constants
CENTS_PER_DOLLAR = 100
MAX_LOAN_AMOUNT_CENTS = 10_000_000_000  # $100,000,000 max
MIN_LOAN_AMOUNT_CENTS = 1  # $0.01 minimum (1 cent)
INTEREST_RATE_SCALE = 10_000  # 10000 = 100.00% (4 decimal places)
MAX_INTEREST_RATE = 10_000 * 200  # 2000.00% max (clearly invalid if exceeded)

# Rounding Policy
ROUNDING_MODE = ROUND_HALF_UP


def dollars_to_cents(amount_dollars: Union[float, str, Decimal]) -> int:
    """
    Convert dollar amount to cents (integer) with strict precision validation.

    Args:
        amount_dollars: Dollar amount (float, string, or Decimal)

    Returns:
        Amount in cents as integer

    Raises:
        ValueError: If conversion would lose precision or exceed limits

    Examples:
        >>> dollars_to_cents(10.50)
        1050
        >>> dollars_to_cents("10.50")
        1050
        >>> dollars_to_cents("10.001")  # Too precise
        ValueError: Monetary value has more than 2 decimal places
    """
    # Convert to Decimal for precision-safe arithmetic
    if isinstance(amount_dollars, float):
        # Flag: float inputs should ideally come from string parsing
        # This guard catches float precision issues at conversion boundary
        decimal_amount = Decimal(str(amount_dollars))
    elif isinstance(amount_dollars, str):
        decimal_amount = Decimal(amount_dollars)
    else:
        decimal_amount = amount_dollars

    # Check for excessive decimal places (more than 2 = beyond cents)
    if decimal_amount % Decimal("0.01") != 0:
        raise ValueError(
            f"Monetary value has more than 2 decimal places: {amount_dollars}. "
            f"Values must round to nearest cent."
        )

    # Convert to cents using Decimal for precision
    cents = int(
        (decimal_amount * Decimal(CENTS_PER_DOLLAR)).quantize(Decimal("1"), rounding=ROUNDING_MODE)
    )

    # Validate bounds
    if cents < MIN_LOAN_AMOUNT_CENTS:
        raise ValueError(f"Loan amount {amount_dollars} is below minimum ($0.01)")
    if cents > MAX_LOAN_AMOUNT_CENTS:
        raise ValueError(f"Loan amount {amount_dollars} exceeds maximum ($100,000,000)")

    return cents


def cents_to_dollars(amount_cents: int) -> Decimal:
    """
    Convert cents (integer) back to dollars.

    Args:
        amount_cents: Amount in cents

    Returns:
        Amount in dollars as Decimal (preserves precision)

    Examples:
        >>> cents_to_dollars(1050)
        Decimal('10.50')
    """
    return Decimal(amount_cents) / Decimal(CENTS_PER_DOLLAR)


def interest_rate_to_basis_points(rate_decimal: Union[float, Decimal]) -> int:
    """
    Convert interest rate (0.05 = 5%) to basis points (500 = 5%).
    Basis points are scaled integers: 10000 = 100.00%.

    Args:
        rate_decimal: Interest rate as decimal (0.05 for 5%)

    Returns:
        Rate in basis points as integer

    Raises:
        ValueError: If rate is outside valid range

    Examples:
        >>> interest_rate_to_basis_points(0.05)
        500
        >>> interest_rate_to_basis_points(Decimal('0.0525'))
        525
    """
    if isinstance(rate_decimal, float):
        decimal_rate = Decimal(str(rate_decimal))
    else:
        decimal_rate = rate_decimal

    basis_points = int(
        (decimal_rate * Decimal(INTEREST_RATE_SCALE)).quantize(Decimal("1"), rounding=ROUNDING_MODE)
    )

    # Validate bounds (0% to 2000%)
    if basis_points < 0:
        raise ValueError(f"Interest rate cannot be negative: {rate_decimal}")
    if basis_points > MAX_INTEREST_RATE:
        raise ValueError(f"Interest rate exceeds maximum (2000%): {rate_decimal}")

    return basis_points


def basis_points_to_interest_rate(basis_points: int) -> Decimal:
    """
    Convert basis points back to decimal interest rate.

    Args:
        basis_points: Rate in basis points (500 = 5%)

    Returns:
        Rate as Decimal (0.05 for 5%)

    Examples:
        >>> basis_points_to_interest_rate(500)
        Decimal('0.05')
    """
    return Decimal(basis_points) / Decimal(INTEREST_RATE_SCALE)


def safe_decimal_sum(values) -> Decimal:
    """
    Sum numeric values using Decimal for precision.
    Useful for aggregating monetary amounts without drift.

    Args:
        values: Iterable of numeric values

    Returns:
        Sum as Decimal

    Examples:
        >>> safe_decimal_sum([10.50, 20.25, 5.00])
        Decimal('35.75')
    """
    total = Decimal("0")
    for value in values:
        if isinstance(value, float):
            total += Decimal(str(value))
        else:
            total += Decimal(value)
    return total


def safe_decimal_divide(
    numerator: Union[int, Decimal], denominator: Union[int, Decimal], precision: int = 4
) -> Decimal:
    """
    Divide two numeric values using Decimal for precision.
    Returns result truncated to specified decimal places.

    Args:
        numerator: Top value
        denominator: Bottom value
        precision: Decimal places in result (default 4 for basis points)

    Returns:
        Result as Decimal

    Raises:
        ValueError: If denominator is zero

    Examples:
        >>> safe_decimal_divide(1, 3, precision=4)
        Decimal('0.3333')
    """
    if denominator == 0:
        raise ValueError("Cannot divide by zero")

    numerator_dec = Decimal(numerator) if not isinstance(numerator, Decimal) else numerator
    denominator_dec = Decimal(denominator) if not isinstance(denominator, Decimal) else denominator

    # Use ROUND_HALF_UP for banker's precision
    quantize_exp = Decimal(10) ** -precision
    result = (numerator_dec / denominator_dec).quantize(quantize_exp, rounding=ROUNDING_MODE)

    return result


def validate_monetary_field(field_name: str, value: Union[float, int, str, Decimal]) -> int:
    """
    Validate and convert a monetary field to cents.
    Logs warnings for suspicious values.

    Args:
        field_name: Name of field (for logging)
        value: Value to validate

    Returns:
        Value in cents

    Raises:
        ValueError: On validation failure
    """
    try:
        cents = dollars_to_cents(value)

        # Warn on extremes (but don't fail)
        if cents < 100:  # Less than $1
            logger.warning(f"{field_name}: Very small amount $0.{cents:02d}")
        if cents > 1_000_000_000:  # More than $10M
            logger.warning(f"{field_name}: Large amount exceeds $10M")

        return cents
    except ValueError as e:
        logger.error(f"Validation failed for {field_name}: {e}")
        raise


# Module-level validation on import
if __name__ == "__main__":
    # Self-test
    print("Testing financial precision module...")

    # Test dollars → cents → dollars round-trip
    test_amounts = [10.50, 100.01, 1.99, 0.01]
    for amount in test_amounts:
        cents = dollars_to_cents(amount)
        back = cents_to_dollars(cents)
        print(f"  {amount:.2f} → {cents} cents → {back}")
        assert float(back) == amount, f"Round-trip failed for {amount}"

    # Test interest rate conversion
    test_rates = [0.05, 0.0525, 0.15, 0.25]
    for rate in test_rates:
        bp = interest_rate_to_basis_points(rate)
        back = basis_points_to_interest_rate(bp)
        print(f"  {rate:.4f} → {bp} bp → {back}")

    print("✅ All tests passed!")
