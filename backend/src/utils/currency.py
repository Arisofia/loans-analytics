from decimal import Decimal, ROUND_HALF_EVEN

def quantize_currency(amount: Decimal | str | int) -> Decimal:
    """Enforce strict Banker's Rounding for all financial metrics."""
    return Decimal(str(amount)).quantize(Decimal('0.00'), rounding=ROUND_HALF_EVEN)
