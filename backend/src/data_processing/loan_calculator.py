from decimal import Decimal
from backend.src.utils.currency import quantize_currency

class LoanAccrualEngine:
    def __init__(self, principal: str, annual_rate: str):
        # Strict casting to Decimal. Floats will trigger a TypeError upstream.
        self.principal = quantize_currency(principal)
        self.daily_rate = Decimal(annual_rate) / Decimal('365')

    def calculate_daily_accrual(self) -> Decimal:
        """
        Calculates daily interest: I = P \times r_{daily}
        """
        accrual = self.principal * self.daily_rate
        return quantize_currency(accrual)
