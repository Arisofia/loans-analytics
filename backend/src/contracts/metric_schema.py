from typing import Dict, Optional

from pydantic import BaseModel


class MetricResult(BaseModel):
    metric_id: str
    metric_name: str
    value: float
    unit: str
    as_of_date: str
    source_mart: str
    owner: str
    quality_status: str = "ok"
    dimension_context: Optional[Dict[str, str]] = None
