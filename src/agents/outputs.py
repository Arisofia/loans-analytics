from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseOutput(ABC):
    @abstractmethod
    def publish(self, content: str, **kwargs: Any) -> bool:
        """Publish content to the respective channel."""

class FigmaOutput(BaseOutput):
    def publish(self, content: str, **kwargs: Any) -> bool:
        # Placeholder for Figma API call
        print(f"[Figma Output] Updating design with content: {content[:50]}...")
        return True
