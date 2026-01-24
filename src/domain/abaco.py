

class AbacoEligibilityEvaluator:
    """
    Implementación oficial de reglas de colateral del BCE
    """

    PD_THRESHOLD_TIER_1 = 0.004
    PD_THRESHOLD_TIER_2 = 0.010
    MIN_AMOUNT_EUR = 500_000.00

    @classmethod
    def evaluate(cls, pd: float, amount: float, currency: str) -> tuple[bool, str]:
        if currency != "EUR":
            return False, "INVALID_CURRENCY"
        if amount < cls.MIN_AMOUNT_EUR:
            return False, "BELOW_MIN_AMOUNT"
        if pd <= cls.PD_THRESHOLD_TIER_1:
            return True, "ELIGIBLE_TIER_1"
        elif pd <= cls.PD_THRESHOLD_TIER_2:
            return True, "ELIGIBLE_TIER_2"
        return False, f"PD_HIGH_{pd}"
