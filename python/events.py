from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
class EventType(str, Enum):
    INGESTION_STARTED = "ingestion_started"
    INGESTION_COMPLETED = "ingestion_completed"
    VALIDATION_FAILED = "validation_failed"
    STATE_TRANSITION = "state_transition"
    KPI_COMPUTED = "kpi_computed"
class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType
    context: Dict[str, Any] = Field(default_factory=dict)
class InvoiceEvent(BaseEvent):
    invoice_id: str
    prev_state: Optional[str] = None
    new_state: str
    actor: str
class KPIEvent(BaseEvent):
    kpi_name: str
    value: float
    dimensions: Dict[str, Any] = Field(default_factory=dict)
def log_event(event: BaseEvent):
    """
    Simulate append-only event logging.
    In production, this would write to a database or event stream (Kafka/Redis).
    """
    # For now, we log to stdout/logger
    print(
        f"[AUDIT_TRAIL] {event.timestamp.isoformat()} | "
        f"{event.event_type} | {event.model_dump_json()}"
    )
