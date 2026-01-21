from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Loan:
    id: str
    amount: float
    interest_rate: float
    status: str
    created_at: datetime

@dataclass
class Portfolio:
    loans: List[Loan]

    @property
    def total_value(self) -> float:
        return sum(loan.amount for loan in self.loans if loan.status == 'active')

    @property
    def average_rate(self) -> float:
        if not self.loans:
            return 0.0
        return sum(loan.interest_rate for loan in self.loans) / len(self.loans)
