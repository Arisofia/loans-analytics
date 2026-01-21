from typing import Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field
import pandas as pd

class LoanRecord(BaseModel):
    """Schema enforcement for individual loan or portfolio records."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    loan_id: Optional[str] = Field(None, alias="loan_id")
    total_receivable_usd: float = Field(ge=0)
    total_eligible_usd: float = Field(ge=0)
    discounted_balance_usd: float = Field(ge=0)
    cash_available_usd: float = Field(default=0.0, ge=0)
    dpd_0_7_usd: float = Field(default=0.0, ge=0)
    dpd_7_30_usd: float = Field(default=0.0, ge=0)
    dpd_30_60_usd: float = Field(default=0.0, ge=0)
    dpd_60_90_usd: float = Field(default=0.0, ge=0)
    dpd_90_plus_usd: float = Field(default=0.0, ge=0)
    measurement_date: Optional[str] = None

@dataclass
class IngestionResult:
    """Container for ingestion outputs and metadata."""
    df: pd.DataFrame
    run_id: str
    metadata: Dict[str, Any]
    source_hash: Optional[str] = None
    raw_path: Optional[str] = None
