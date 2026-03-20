"""Canonical multi-agent namespace under src/agents.

DEPRECATED: This module is a shim for backward compatibility. 
Please import from `backend.python.multi_agent` directly.
"""

import warnings
from backend.python.multi_agent import (
    ComplianceAgent,
    CustomerRetentionAgent,
    DatabaseDesignerAgent,
    GrowthStrategistAgent,
    RiskAnalystAgent,
    CollectionsAgent,
    FraudDetectionAgent,
    PricingAgent,
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
    AgentTracer,
    Guardrails,
    BaseAgent,
    MultiAgentOrchestrator,
)

# Emit deprecation warning on import
warnings.warn(
    "Importing from `backend.src.agents.multi_agent` is deprecated and will be removed in Q2 2026. "
    "Please import from `backend.python.multi_agent` directly.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
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
    "MultiAgentOrchestrator",
]
