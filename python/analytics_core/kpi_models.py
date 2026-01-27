from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class KPIType(str, Enum):
    RATIO = "ratio"
    COUNT = "count"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DURATION = "duration"
    SCORE = "score"
    OTHER = "other"


class KPILevel(str, Enum):
    PORTFOLIO = "portfolio"
    PRODUCT = "product"
    SEGMENT = "segment"
    CUSTOMER = "customer"
    OPERATIONAL = "operational"
    SYSTEM = "system"


class KPIValue(BaseModel):
    value: float
    unit: Optional[str] = None
    currency: Optional[str] = None
    as_of: datetime = Field(default_factory=datetime.utcnow)


class KPI(BaseModel):
    id: str
    name: str
    description: str
    kpi_type: KPIType
    level: KPILevel
    value: KPIValue
    tags: List[str] = Field(default_factory=list)
    formula: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class KPISet(BaseModel):
    id: str
    name: str
    description: str
    category: str
    as_of: datetime = Field(default_factory=datetime.utcnow)
    kpis: List[KPI] = Field(default_factory=list)

    def to_dict(self) -> Dict:
        return self.model_dump()


class KPIError(BaseModel):
    kpi_id: str
    message: str
    details: Optional[Dict] = None
