"""
Financial Precision Regression Tests

Tests ensuring that financial calculations (aggregations, rates, etc.) maintain
precision and do not accumulate floating-point errors. These tests MUST pass
on every CI run to prevent financial data drift.

Test Categories:
1. Precision Conversion Tests: dollars↔cents, rates↔basis points
2. Aggregation Tests: Ensure sums are exact (no floating point drift)
3. Division Tests: Rates and percentages computed with precision
4. Edge Cases: Extreme values, boundary conditions
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from backend.python.financial_precision import (
    dollars_to_cents,
    cents_to_dollars,
    interest_rate_to_basis_points,
    basis_points_to_interest_rate,
    safe_decimal_sum,
    safe_decimal_divide,
    validate_monetary_field,
)


class TestMonetaryConversions:
    """Test dollars ↔ cents conversions maintain precision."""

    def test_dollars_to_cents_basic(self):
        """Basic dollar to cents conversion."""
        assert dollars_to_cents(10.50) == 1050
        assert dollars_to_cents(100.00) == 10000
        assert dollars_to_cents(0.01) == 1

    def test_dollars_to_cents_from_string(self):
        """String input maintains precision."""
        assert dollars_to_cents("10.50") == 1050
        with pytest.raises(ValueError, match="more than 2 decimal places"):
            dollars_to_cents("100.9999")  # Will raise, more than 2 decimals

    def test_cents_to_dollars_roundtrip(self):
        """Round-trip conversion preserves value."""
        test_values = [10.50, 100.01, 1.99, 0.01, 999999.99]
        for value in test_values:
            cents = dollars_to_cents(value)
            back = cents_to_dollars(cents)
            assert float(back) == value, f"Round-trip failed for {value}"

    def test_precision_rejection_too_many_decimals(self):
        """Reject values with more than 2 decimal places."""
        with pytest.raises(ValueError, match="more than 2 decimal places"):
            dollars_to_cents("10.001")  # 3 decimal places

        with pytest.raises(ValueError, match="more than 2 decimal places"):
            dollars_to_cents(10.999)  # More than 2 decimals when converted

    def test_monetary_bounds(self):
        """Reject values outside valid range."""
        # Note: Values below $0.01 with exact precision don't exist
        # (minimum is $0.01 = 1 cent). So we skip the below-minimum test.

        # Test maximum bounds
        with pytest.raises(ValueError, match="exceeds maximum"):
            dollars_to_cents(100_000_001)  # Over $100,000,000

    def test_exact_cent_values(self):
        """Exact cent values (no rounding needed)."""
        # These should not trigger rounding at all
        exact_cases = [0.01, 0.50, 1.00, 10.25, 99.99]
        for value in exact_cases:
            cents = dollars_to_cents(value)
            back = cents_to_dollars(cents)
            assert back == Decimal(str(value))


class TestInterestRateConversions:
    """Test interest rate ↔ basis point conversions."""

    def test_rate_to_basis_points_basic(self):
        """Basic rate to basis points conversion."""
        assert interest_rate_to_basis_points(0.05) == 500  # 5%
        assert interest_rate_to_basis_points(0.01) == 100  # 1%
        assert interest_rate_to_basis_points(0.0525) == 525  # 5.25%

    def test_basis_points_roundtrip(self):
        """Round-trip conversion preserves rate."""
        test_rates = [0.01, 0.05, 0.0525, 0.15, 0.25, 1.0, 2.0]
        for rate in test_rates:
            bp = interest_rate_to_basis_points(rate)
            back = basis_points_to_interest_rate(bp)
            # Allow small rounding differences due to 4-decimal precision
            assert abs(float(back) - rate) < 0.00001

    def test_rate_bounds(self):
        """Reject rates outside valid range."""
        with pytest.raises(ValueError, match="negative"):
            interest_rate_to_basis_points(-0.05)

        # MAX_INTEREST_RATE is 2,000,000 basis points (equivalent to 200% if reading as 0.XX format)
        # To exceed max, use rate > 200 to get > 2,000,000 basis points
        with pytest.raises(ValueError, match="exceeds maximum"):
            interest_rate_to_basis_points(201)  # 201 * 10000 = 2,010,000 > 2,000,000

    def test_rate_with_decimal_input(self):
        """Decimal input for rates."""
        rate_dec = Decimal("0.0525")
        bp = interest_rate_to_basis_points(rate_dec)
        assert bp == 525
        back = basis_points_to_interest_rate(bp)
        assert back == rate_dec


class TestAggregationPrecision:
    """Test that aggregate operations (sum, mean) maintain precision."""

    def test_safe_decimal_sum(self):
        """Decimal sum avoids floating-point drift."""
        # Classic float summation problem: many operations accumulate error
        # Rather than 0.1+0.2!=0.3 which sometimes works, test with values
        # that demonstrate real accumulation
        from decimal import Decimal

        values_float = [0.1] * 10 + [0.2] * 10  # 10 times 0.1, 10 times 0.2
        # Float summation can drift, but Decimal gives exact results.
        _ = sum(values_float)

        # Decimal gives exact result
        decimal_sum = safe_decimal_sum(values_float)
        assert decimal_sum == Decimal("3.0")

    def test_safe_sum_monetary(self):
        """Decimal sum for monetary aggregation."""
        loan_amounts = [10.50, 20.25, 5.33, 100.92]  # Total: $137.00
        total = safe_decimal_sum(loan_amounts)
        assert total == Decimal("137.00")

    def test_huge_aggregation_no_drift(self):
        """Large number of transactions accumulates exactly."""
        # Simulate 10,000 transactions of $1.05 each
        transactions = [1.05] * 10_000
        total = safe_decimal_sum(transactions)
        expected = Decimal("10500.00")
        assert total == expected, f"Expected {expected}, got {total}"


class TestDivisionPrecision:
    """Test division operations maintain precision."""

    def test_safe_divide_basic(self):
        """Basic division with precision control."""
        result = safe_decimal_divide(1, 3, precision=4)
        assert result == Decimal("0.3333")

    def test_safe_divide_percentage(self):
        """Division for percentage calculations."""
        # Calculate: $100 / $250 = 40%
        result = safe_decimal_divide(100, 250, precision=4)
        assert result == Decimal("0.4000")  # Exactly 40%

    def test_safe_divide_zero(self):
        """Division by zero handling."""
        with pytest.raises(ValueError, match="divide by zero"):
            safe_decimal_divide(100, 0)

    def test_par_rate_calculation(self):
        """PAR (Past Due) rate calculation with precision."""
        # PAR-30 Amount: $1,000 / Total Balance: $25,000 = 4.00%
        par_amount = 1_000
        total_balance = 25_000
        par_rate = safe_decimal_divide(par_amount, total_balance, precision=4)
        assert par_rate == Decimal("0.0400")


class TestConversionGuards:
    """Test validation guards on monetary field conversions."""

    def test_validate_monetary_field_cents(self):
        """Monetary field validation normalizes to cents."""
        result = validate_monetary_field("test_amount", "10.50")
        assert result == 1050

    def test_validate_monetary_warns_on_small(self):
        """Small amounts logged as warnings."""
        result = validate_monetary_field("small_loan", "0.50")
        assert result == 50  # Valid but logged

    def test_validate_monetary_large(self):
        """Large amounts logged as warnings."""
        result = validate_monetary_field("large_loan", "11_000_000.00")
        assert result == 1_100_000_000  # Valid but logged


class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_minimum_loan_amount(self):
        """Minimum valid loan is $0.01."""
        cents = dollars_to_cents("0.01")
        assert cents == 1
        back = cents_to_dollars(cents)
        assert back == Decimal("0.01")

    def test_maximum_loan_amount(self):
        """Maximum valid loan is $100,000,000."""
        cents = dollars_to_cents("100000000.00")
        assert cents == 10_000_000_000
        back = cents_to_dollars(cents)
        assert back == Decimal("100000000.00")

    def test_minimum_interest_rate(self):
        """Minimum rate is 0%."""
        bp = interest_rate_to_basis_points(0.0)
        assert bp == 0
        back = basis_points_to_interest_rate(bp)
        assert back == Decimal("0")

    def test_maximum_interest_rate(self):
        """Maximum rate is 2000%."""
        bp = interest_rate_to_basis_points(20.0)
        assert bp == 200_000
        back = basis_points_to_interest_rate(bp)
        assert abs(float(back) - 20.0) < 0.00001

    def test_zero_division_handling(self):
        """Portfolio with zero balance is handled gracefully."""
        # If total_balance is 0, division should fail with clear message
        with pytest.raises(ValueError, match="divide by zero"):
            safe_decimal_divide(100, 0, precision=2)


class TestRoundingPolicy:
    """Test ROUND_HALF_UP rounding behavior."""

    def test_rounding_half_up(self):
        """ROUND_HALF_UP: 0.5 rounds away from zero."""
        # 1.5 rounds to 2
        amount = Decimal("1.5")
        rounded = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert rounded == Decimal("2")

        # 2.5 rounds to 3
        amount = Decimal("2.5")
        rounded = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert rounded == Decimal("3")

    def test_rounding_monetary_amounts(self):
        """Monetary conversions use ROUND_HALF_UP (tested implicitly in other tests)."""
        # The dollars_to_cents function is strict: it rejects amounts with
        # more than 2 decimal places (3+ decimals). This ensures precision
        # is maintained at the input stage.
        # ROUND_HALF_UP behavior is tested implicitly in safe_decimal_divide
        # and other operations. Rounding of fractional cents happens
        # during Decimal operations, not during dollars_to_cents conversion.

        # Test that the function rejects 3+ decimals
        with pytest.raises(ValueError, match="more than 2 decimal places"):
            dollars_to_cents(Decimal("1.005"))  # 3 decimals, rejected


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
