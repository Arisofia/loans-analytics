"""Agent tracing and observability."""

import hashlib
import time
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

from python.logging_config import get_logger
from python.time_utils import get_iso_timestamp

from .protocol import AgentError, AgentRequest, AgentResponse, AgentRole

logger = get_logger(__name__)


class AgentTracer:
    """Centralized tracing, logging, and cost tracking."""

    def __init__(self, enable_otel: bool = False):
        self.enable_otel = enable_otel and OTEL_AVAILABLE
        self.tracer = trace.get_tracer(__name__) if self.enable_otel else None
        self._cost_accumulator: dict[str, float] = {}
        self._token_accumulator: dict[str, int] = {}

    @staticmethod
    def generate_trace_id(prefix: str = "trace") -> str:
        """Generate unique trace ID."""
        timestamp = str(time.time_ns())
        return f"{prefix}_{hashlib.sha256(timestamp.encode()).hexdigest()[:16]}"

    def start_trace(self, agent_role: AgentRole, request: AgentRequest) -> Any | None:
        """Start trace span."""
        if not self.enable_otel or not self.tracer:
            return None

        span = self.tracer.start_span(
            name=f"agent.{agent_role.value}",
            attributes={
                "trace_id": request.trace_id,
                "session_id": request.session_id or "",
                "user_id": request.user_id or "",
                "agent_role": agent_role.value,
                "message_count": len(request.messages),
            },
        )
        return span

    def end_trace(
        self,
        span: Any | None,
        response: AgentResponse | None = None,
        error: Exception | None = None,
    ):
        """End trace span."""
        if not span:
            return

        if error:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)
        elif response:
            span.set_attribute("tokens_used", response.tokens_used)
            span.set_attribute("cost_usd", response.cost_usd)
            span.set_attribute("latency_ms", response.latency_ms)
            span.set_status(Status(StatusCode.OK))

        span.end()

    def log_request(self, agent_role: AgentRole, request: AgentRequest):
        """Log agent request."""
        logger.info(
            "agent_request",
            extra={
                "trace_id": request.trace_id,
                "session_id": request.session_id,
                "agent_role": agent_role.value,
                "message_count": len(request.messages),
                "context_keys": list(request.context.keys()),
                "timestamp": get_iso_timestamp(),
            },
        )

    def log_response(self, response: AgentResponse):
        """Log agent response."""
        logger.info(
            "agent_response",
            extra={
                "trace_id": response.trace_id,
                "agent_role": response.agent_role.value,
                "tokens_used": response.tokens_used,
                "cost_usd": response.cost_usd,
                "latency_ms": response.latency_ms,
                "provider": response.provider.value,
                "model": response.model,
                "timestamp": response.timestamp.isoformat(),
            },
        )

        self._cost_accumulator[response.trace_id] = (
            self._cost_accumulator.get(response.trace_id, 0.0) + response.cost_usd
        )
        self._token_accumulator[response.trace_id] = (
            self._token_accumulator.get(response.trace_id, 0) + response.tokens_used
        )

    def log_error(self, error: AgentError):
        """Log agent error."""
        logger.error(
            "agent_error",
            extra={
                "trace_id": error.trace_id,
                "agent_role": error.agent_role.value,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "timestamp": error.timestamp.isoformat(),
            },
        )

    def get_trace_cost(self, trace_id: str) -> float:
        """Get accumulated cost for trace."""
        return self._cost_accumulator.get(trace_id, 0.0)

    def get_trace_tokens(self, trace_id: str) -> int:
        """Get accumulated tokens for trace."""
        return self._token_accumulator.get(trace_id, 0)

    def reset_trace(self, trace_id: str):
        """Reset accumulators for trace."""
        self._cost_accumulator.pop(trace_id, None)
        self._token_accumulator.pop(trace_id, None)
