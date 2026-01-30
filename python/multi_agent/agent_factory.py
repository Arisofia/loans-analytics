"""Factory utilities to reduce agent boilerplate code."""

from .base_agent import BaseAgent
from .protocol import AgentRole, LLMProvider


def agent_with_role(role: AgentRole):
    """
    Decorator to automatically add __init__ method to agent classes.

    Usage:
        @agent_with_role(AgentRole.RISK_ANALYST)
        class RiskAnalystAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "..."

    Args:
        role: The agent's role

    Returns:
        Decorated class with automatic __init__
    """

    def decorator(cls):
        """Add __init__ to the class."""

        def new_init(self, provider: LLMProvider = LLMProvider.OPENAI, **kwargs):
            """Initialize agent with specified role."""
            # Remove role from kwargs if present to avoid duplicate argument error
            kwargs.pop("role", None)
            # Call BaseAgent.__init__ directly
            BaseAgent.__init__(self, role=role, provider=provider, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator
