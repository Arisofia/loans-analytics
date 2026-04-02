from .base_agent import BaseAgent
from .protocol import AgentRole, LLMProvider

def agent_with_role(role: AgentRole):

    def decorator(cls):

        def new_init(self, provider: LLMProvider=LLMProvider.OPENAI, **kwargs):
            kwargs.pop('role', None)
            BaseAgent.__init__(self, role=role, provider=provider, **kwargs)
        cls.__init__ = new_init
        return cls
    return decorator
