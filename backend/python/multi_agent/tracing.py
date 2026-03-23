import uuid
from typing import Any, Dict, Optional
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
from backend.python.logging_config import get_logger
from backend.python.time_utils import get_iso_timestamp
from .protocol import AgentError, AgentRequest, AgentResponse, AgentRole
logger = get_logger(__name__)

class AgentTracer:

    def __init__(self, enable_otel: bool=False):
        self.enable_otel = enable_otel and OTEL_AVAILABLE
        self.tracer = trace.get_tracer(__name__) if self.enable_otel else None
        self._cost_accumulator: Dict[str, float] = {}
        self._token_accumulator: Dict[str, int] = {}

    @staticmethod
    def generate_trace_id(prefix: str='trace') -> str:
        return f'{prefix}_{uuid.uuid4().hex[:16]}'

    def start_trace(self, agent_role: AgentRole, request: AgentRequest) -> Optional[Any]:
        if not self.enable_otel or not self.tracer:
            return None
        return self.tracer.start_span(name=f'agent.{agent_role.value}', attributes={'trace_id': request.trace_id, 'session_id': request.session_id or '', 'user_id': request.user_id or '', 'agent_role': agent_role.value, 'message_count': len(request.messages)})

    def end_trace(self, span: Optional[Any], response: Optional[AgentResponse]=None, error: Optional[Exception]=None):
        if not span:
            return
        if error:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)
        elif response:
            span.set_attribute('tokens_used', response.tokens_used)
            span.set_attribute('cost_usd', response.cost_usd)
            span.set_attribute('latency_ms', response.latency_ms)
            span.set_status(Status(StatusCode.OK))
        span.end()

    def log_request(self, agent_role: AgentRole, request: AgentRequest):
        logger.info('agent_request', extra={'trace_id': request.trace_id, 'session_id': request.session_id, 'agent_role': agent_role.value, 'message_count': len(request.messages), 'context_keys': list(request.context.keys()), 'timestamp': get_iso_timestamp()})

    def log_response(self, response: AgentResponse):
        logger.info('agent_response', extra={'trace_id': response.trace_id, 'agent_role': response.agent_role.value, 'tokens_used': response.tokens_used, 'cost_usd': response.cost_usd, 'latency_ms': response.latency_ms, 'provider': response.provider.value, 'model': response.model, 'timestamp': response.timestamp.isoformat()})
        self._cost_accumulator[response.trace_id] = self._cost_accumulator.get(response.trace_id, 0.0) + response.cost_usd
        self._token_accumulator[response.trace_id] = self._token_accumulator.get(response.trace_id, 0) + response.tokens_used

    def log_error(self, error: AgentError):
        logger.error('agent_error', extra={'trace_id': error.trace_id, 'agent_role': error.agent_role.value, 'error_type': error.error_type, 'error_message': error.error_message, 'timestamp': error.timestamp.isoformat()})

    def get_trace_cost(self, trace_id: str) -> float:
        return self._cost_accumulator.get(trace_id, 0.0)

    def get_trace_tokens(self, trace_id: str) -> int:
        return self._token_accumulator.get(trace_id, 0)

    def reset_trace(self, trace_id: str):
        self._cost_accumulator.pop(trace_id, None)
        self._token_accumulator.pop(trace_id, None)
