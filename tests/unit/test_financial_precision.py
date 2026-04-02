import pytest
from decimal import Decimal, ROUND_HALF_UP
from backend.loans_analytics.financial_precision import dollars_to_cents, cents_to_dollars, interest_rate_to_basis_points, basis_points_to_interest_rate, safe_decimal_sum, safe_decimal_divide, validate_monetary_field

class TestMonetaryConversions:

    def test_dollars_to_cents_basic(self):
        assert dollars_to_cents(10.5) == 1050
        assert dollars_to_cents(100.0) == 10000
        assert dollars_to_cents(0.01) == 1

    def test_dollars_to_cents_from_string(self):
        assert dollars_to_cents('10.50') == 1050
        with pytest.raises(ValueError, match='more than 2 decimal places'):
            dollars_to_cents('100.9999')

    def test_cents_to_dollars_roundtrip(self):
        test_values = [10.5, 100.01, 1.99, 0.01, 999999.99]
        for value in test_values:
            cents = dollars_to_cents(value)
            back = cents_to_dollars(cents)
            assert float(back) == value, f'Round-trip failed for {value}'

    def test_precision_rejection_too_many_decimals(self):
        with pytest.raises(ValueError, match='more than 2 decimal places'):
            dollars_to_cents('10.001')
        with pytest.raises(ValueError, match='more than 2 decimal places'):
            dollars_to_cents(10.999)

    def test_monetary_bounds(self):
        with pytest.raises(ValueError, match='exceeds maximum'):
            dollars_to_cents(100000001)

    def test_exact_cent_values(self):
        exact_cases = [0.01, 0.5, 1.0, 10.25, 99.99]
        for value in exact_cases:
            cents = dollars_to_cents(value)
            back = cents_to_dollars(cents)
            assert back == Decimal(str(value))

class TestInterestRateConversions:

    def test_rate_to_basis_points_basic(self):
        assert interest_rate_to_basis_points(0.05) == 500
        assert interest_rate_to_basis_points(0.01) == 100
        assert interest_rate_to_basis_points(0.0525) == 525

    def test_basis_points_roundtrip(self):
        test_rates = [0.01, 0.05, 0.0525, 0.15, 0.25, 1.0, 2.0]
        for rate in test_rates:
            bp = interest_rate_to_basis_points(rate)
            back = basis_points_to_interest_rate(bp)
            assert abs(float(back) - rate) < 1e-05

    def test_rate_bounds(self):
        with pytest.raises(ValueError, match='negative'):
            interest_rate_to_basis_points(-0.05)
        with pytest.raises(ValueError, match='exceeds maximum'):
            interest_rate_to_basis_points(201)

    def test_rate_with_decimal_input(self):
        rate_dec = Decimal('0.0525')
        bp = interest_rate_to_basis_points(rate_dec)
        assert bp == 525
        back = basis_points_to_interest_rate(bp)
        assert back == rate_dec

class TestAggregationPrecision:

    def test_safe_decimal_sum(self):
        from decimal import Decimal
        values_float = [0.1] * 10 + [0.2] * 10
        _ = sum(values_float)
        decimal_sum = safe_decimal_sum(values_float)
        assert decimal_sum == Decimal('3.0')

    def test_safe_sum_monetary(self):
        loan_amounts = [10.5, 20.25, 5.33, 100.92]
        total = safe_decimal_sum(loan_amounts)
        assert total == Decimal('137.00')

    def test_huge_aggregation_no_drift(self):
        transactions = [1.05] * 10000
        total = safe_decimal_sum(transactions)
        expected = Decimal('10500.00')
        assert total == expected, f'Expected {expected}, got {total}'

class TestDivisionPrecision:

    def test_safe_divide_basic(self):
        result = safe_decimal_divide(1, 3, precision=4)
        assert result == Decimal('0.3333')

    def test_safe_divide_percentage(self):
        result = safe_decimal_divide(100, 250, precision=4)
        assert result == Decimal('0.4000')

    def test_safe_divide_zero(self):
        with pytest.raises(ValueError, match='divide by zero'):
            safe_decimal_divide(100, 0)

    def test_par_rate_calculation(self):
        par_amount = 1000
        total_balance = 25000
        par_rate = safe_decimal_divide(par_amount, total_balance, precision=4)
        assert par_rate == Decimal('0.0400')

class TestConversionGuards:

    def test_validate_monetary_field_cents(self):
        result = validate_monetary_field('test_amount', '10.50')
        assert result == 1050

    def test_validate_monetary_warns_on_small(self):
        result = validate_monetary_field('small_loan', '0.50')
        assert result == 50

    def test_validate_monetary_large(self):
        result = validate_monetary_field('large_loan', '11_000_000.00')
        assert result == 1100000000

class TestEdgeCases:

    def test_minimum_loan_amount(self):
        cents = dollars_to_cents('0.01')
        assert cents == 1
        back = cents_to_dollars(cents)
        assert back == Decimal('0.01')

    def test_maximum_loan_amount(self):
        cents = dollars_to_cents('100000000.00')
        assert cents == 10000000000
        back = cents_to_dollars(cents)
        assert back == Decimal('100000000.00')

    def test_minimum_interest_rate(self):
        bp = interest_rate_to_basis_points(0.0)
        assert bp == 0
        back = basis_points_to_interest_rate(bp)
        assert back == Decimal('0')

    def test_maximum_interest_rate(self):
        bp = interest_rate_to_basis_points(20.0)
        assert bp == 200000
        back = basis_points_to_interest_rate(bp)
        assert abs(float(back) - 20.0) < 1e-05

    def test_zero_division_handling(self):
        with pytest.raises(ValueError, match='divide by zero'):
            safe_decimal_divide(100, 0, precision=2)

class TestRoundingPolicy:

    def test_rounding_half_up(self):
        amount = Decimal('1.5')
        rounded = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        assert rounded == Decimal('2')
        amount = Decimal('2.5')
        rounded = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        assert rounded == Decimal('3')

    def test_rounding_monetary_amounts(self):
        with pytest.raises(ValueError, match='more than 2 decimal places'):
            dollars_to_cents(Decimal('1.005'))
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
