"""Typed protocol for multi-agent system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:
    from pydantic import BaseModel, Field
    from pydantic import validator as field_validator


class AgentRole(str, Enum):
    """Standard agent roles."""

    RISK_ANALYST = "risk_analyst"
    GROWTH_STRATEGIST = "growth_strategist"
    OPS_OPTIMIZER = "ops_optimizer"
    COMPLIANCE = "compliance"
    ORCHESTRATOR = "orchestrator"
    LEGACY = "legacy"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class MessageRole(str, Enum):
    """Message role in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Single message in conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Tool(BaseModel):
    """Agent tool definition."""

    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class AgentRequest(BaseModel):
    """Request to an agent."""

    trace_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    messages: List[Message]
    context: Dict[str, Any] = Field(default_factory=dict)
    tools: List[Tool] = Field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""

    trace_id: str
    agent_role: AgentRole
    message: Message
    context: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4o-mini"
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentError(BaseModel):
    """Error from agent execution."""

    trace_id: str
    agent_role: AgentRole
    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScenarioStep(BaseModel):
    """Single step in orchestrated scenario."""

    agent_role: AgentRole
    prompt_template: str
    context_keys: List[str] = Field(default_factory=list)
    output_key: str
    optional: bool = False


class Scenario(BaseModel):
    """Multi-agent orchestration scenario."""

    name: str
    description: str
    steps: List[ScenarioStep]
    initial_context: Dict[str, Any] = Field(default_factory=dict)
