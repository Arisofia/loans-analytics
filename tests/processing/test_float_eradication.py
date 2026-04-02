from decimal import Decimal
from backend.src.data_processing.loan_calculator import LoanAccrualEngine

def test_daily_accrual_precision():
    """Inject $100.03 with a highly fractional rate and assert the output matches exact deterministic ledger values, not 100.030000000001."""
    principal = "100.03"
    annual_rate = "0.15"  # 15%
    
    engine = LoanAccrualEngine(principal, annual_rate)
    accrual = engine.calculate_daily_accrual()
    
    # Expected: 100.03 * (0.15 / 365) = 15.0045 / 365 = 0.041108219...
    # ROUND_HALF_EVEN (Banker's rounding) to 2 decimals: 0.04
    assert accrual == Decimal('0.04')

def test_rounding_boundary():
    # Banker's rounding (ROUND_HALF_EVEN): 
    # 0.045 -> 0.04
    # 0.055 -> 0.06
    # 0.041... -> 0.04
    
    # Let's test with a value that should round to 0.04
    principal = "100.00"
    annual_rate = str(Decimal('0.045') * 365 / 100) # Should result in 0.045 accrual before rounding
    
    engine = LoanAccrualEngine(principal, annual_rate)
    # 100.00 * (0.045 * 365 / 100) / 365 = 0.045
    # Banker's rounding: 0.045 -> 0.04
    assert engine.calculate_daily_accrual() == Decimal('0.04')
    
    # Let's test with a value that should round to 0.06
    principal = "100.00"
    annual_rate = str(Decimal('0.055') * 365 / 100)
    engine = LoanAccrualEngine(principal, annual_rate)
    # Banker's rounding: 0.055 -> 0.06
    assert engine.calculate_daily_accrual() == Decimal('0.06')
