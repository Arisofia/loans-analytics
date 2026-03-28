"""Multi-agent package — first live slice + legacy compatibility."""

from .orchestrator import MultiAgentOrchestrator
try:
    from .orchestrator import DecisionOrchestrator  # new primary name
except ImportError:
    DecisionOrchestrator = MultiAgentOrchestrator
from .llm_agents import (
    ComplianceAgent,
    CustomerRetentionAgent,
    DatabaseDesignerAgent,
    GrowthStrategistAgent,
    RiskAnalystAgent,
    CollectionsAgent,
    FraudDetectionAgent,
    PricingAgent,
    OpsOptimizerAgent,
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
    "OpsOptimizerAgent",
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
