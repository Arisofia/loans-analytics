from __future__ import annotations

import abc
from typing import Any

import pandas as pd

from backend.src.contracts.agent_schema import AgentOutput


class BaseAgent(abc.ABC):
    @property
    @abc.abstractmethod
    def agent_id(self) -> str:
        """Stable agent identifier."""
        ...

    @abc.abstractmethod
    def run(
        self,
        marts: dict[str, pd.DataFrame],
        metrics: dict[str, Any],
        features: dict[str, pd.DataFrame],
        quality: dict[str, Any],
    ) -> AgentOutput:
        """Execute agent logic and return structured output."""
        ...
