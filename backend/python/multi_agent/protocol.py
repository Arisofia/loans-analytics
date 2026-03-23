from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.python.time_utils import get_utc_now

class AgentRole(str, Enum):
    RISK_ANALYST = 'risk_analyst'
    GROWTH_STRATEGIST = 'growth_strategist'
    OPS_OPTIMIZER = 'ops_optimizer'
    COMPLIANCE = 'compliance'
    COLLECTIONS = 'collections'
    FRAUD_DETECTION = 'fraud_detection'
    PRICING = 'pricing'
    CUSTOMER_RETENTION = 'customer_retention'
    DATABASE_DESIGNER = 'database_designer'
    ORCHESTRATOR = 'orchestrator'
    LEGACY = 'legacy'

class LLMProvider(str, Enum):
    OPENAI = 'openai'
    GEMINI = 'gemini'
    GROK = 'grok'

class MessageRole(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    TOOL = 'tool'

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=get_utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

class AgentRequest(BaseModel):
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
    trace_id: str
    agent_role: AgentRole
    message: Message
    context: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = 'gpt-4o'
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=get_utc_now)

class AgentError(BaseModel):
    trace_id: str
    agent_role: AgentRole
    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=get_utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScenarioStep(BaseModel):
    agent_role: AgentRole
    prompt_template: str
    context_keys: List[str] = Field(default_factory=list)
    output_key: str
    optional: bool = False

class Scenario(BaseModel):
    name: str
    description: str
    steps: List[ScenarioStep]
    initial_context: Dict[str, Any] = Field(default_factory=dict)
