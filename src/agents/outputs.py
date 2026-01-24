from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseOutput(ABC):
    @abstractmethod
    def publish(self, content: str, **kwargs: Any) -> bool:
        """Publish content to the respective channel."""
