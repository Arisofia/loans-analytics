"""Factory utilities to reduce agent boilerplate code."""

from typing import Type

from .base_agent import BaseAgent
from .protocol import AgentRole, LLMProvider


def create_agent_class(role: AgentRole, base_class: Type[BaseAgent] = BaseAgent):
    """
    Create an agent class with automatic __init__ method.

    This eliminates boilerplate code in agent definitions by automatically
    generating the __init__ method that sets the agent role.

    Args:
        role: The agent's role
        base_class: Base class to inherit from (defaults to BaseAgent)

    Returns:
        A mixin class that provides the __init__ method
    """
    class AgentMixin:
        """Mixin that provides standardized __init__ for agents."""

        def __init__(self, provider: LLMProvider = LLMProvider.OPENAI, **kwargs):
            """Initialize agent with specified role."""
            super().__init__(role=role, provider=provider, **kwargs)

    return AgentMixin


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
        original_init = cls.__init__ if hasattr(cls, '__init__') else None

        def new_init(self, provider: LLMProvider = LLMProvider.OPENAI, **kwargs):
            """Initialize agent with specified role."""
            # Call BaseAgent.__init__
            BaseAgent.__init__(self, role=role, provider=provider, **kwargs)
            # Call original __init__ if it exists and does more than just super()
            if original_init and original_init != BaseAgent.__init__:
                original_init(self, provider=provider, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator
