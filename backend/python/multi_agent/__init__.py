"""Multi-agent package — first live slice + legacy compatibility."""

from .orchestrator import DecisionOrchestrator
try:
    from .orchestrator import MultiAgentOrchestrator  # legacy re-export
except ImportError:
    pass
from .llm_agents import (
    ComplianceAgent,
    CustomerRetentionAgent,
    DatabaseDesignerAgent,
    GrowthStrategistAgent,
    RiskAnalystAgent,
    CollectionsAgent,
    FraudDetectionAgent,
    PricingAgent,
)
from .protocol import (
    AgentRole,
    AgentRequest,
    AgentResponse,
    AgentError,
    LLMProvider,
    Message,
    MessageRole,
    Scenario,
    ScenarioStep,
    Tool,
)
from .base_agent import BaseAgent
from .tracing import AgentTracer
from .guardrails import Guardrails

__all__ = [
    "DecisionOrchestrator",
    "MultiAgentOrchestrator",
    "ComplianceAgent",
    "CustomerRetentionAgent",
    "DatabaseDesignerAgent",
    "GrowthStrategistAgent",
    "RiskAnalystAgent",
    "CollectionsAgent",
    "FraudDetectionAgent",
    "PricingAgent",
    "AgentRole",
    "AgentRequest",
    "AgentResponse",
    "AgentError",
    "LLMProvider",
    "Message",
    "MessageRole",
    "Scenario",
    "ScenarioStep",
    "Tool",
    "AgentTracer",
    "Guardrails",
    "BaseAgent",
]
