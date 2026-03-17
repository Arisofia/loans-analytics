"""Pydantic models for the self-healing monitoring and command layer."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class CommandStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# --- Event Models ---


class OperationalEventCreate(BaseModel):
    event_type: str = Field(
        ...,
        description="Type of operational event",
        examples=["pipeline_complete", "kpi_breach", "risk_alert", "sentry_issue"],
    )
    severity: EventSeverity = Field(..., description="Event severity level")
    source: str = Field(
        ...,
        description="System that emitted the event",
        examples=["pipeline", "agent", "sentry", "cron"],
    )
    correlation_id: Optional[UUID] = Field(
        None, description="Correlation ID linking to Sentry traces"
    )
    payload: Dict[str, Any] = Field(default_factory=dict, description="Flexible event data")


class OperationalEventResponse(BaseModel):
    id: UUID = Field(..., description="Event unique identifier")
    event_type: str
    severity: EventSeverity
    source: str
    correlation_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    acknowledged_at: Optional[datetime] = None


class EventsListResponse(BaseModel):
    events: List[OperationalEventResponse]
    count: int = Field(..., description="Total number of events returned")


class EventAcknowledgeRequest(BaseModel):
    event_id: UUID = Field(..., description="Operational event ID to acknowledge")


# --- Command Models ---


class CommandCreate(BaseModel):
    command_type: str = Field(
        ...,
        description="Type of command to execute",
        examples=["rerun_pipeline", "notify_team", "scale_up", "acknowledge_alert"],
    )
    requested_by: str = Field(
        ...,
        description="Who requested the command",
        examples=["n8n", "operator", "auto_rule"],
    )
    event_id: Optional[UUID] = Field(None, description="Related operational event ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command arguments")


class CommandUpdate(BaseModel):
    status: CommandStatus = Field(..., description="New command status")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result payload")


class CommandResponse(BaseModel):
    id: UUID = Field(..., description="Command unique identifier")
    command_type: str
    status: CommandStatus
    requested_by: str
    event_id: Optional[UUID] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CommandsListResponse(BaseModel):
    commands: List[CommandResponse]
    count: int = Field(..., description="Total number of commands returned")
