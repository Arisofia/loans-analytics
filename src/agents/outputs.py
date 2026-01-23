from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseOutput(ABC):
    @abstractmethod
    def publish(self, content: str, **kwargs: Any) -> bool:
        """Publish content to the respective channel."""


class SlackOutput(BaseOutput):
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def publish(self, content: str, **kwargs: Any) -> bool:
        # Placeholder for Slack webhook/API call
        print(f"[Slack Output] Publishing: {content[:50]}...")
        return True


class NotionOutput(BaseOutput):
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        self.api_key = api_key
        self.database_id = database_id

    def publish(self, content: str, **kwargs: Any) -> bool:
        # Placeholder for Notion API call
        print(f"[Notion Output] Creating page with content: {content[:50]}...")
        return True


class FigmaOutput(BaseOutput):
    def publish(self, content: str, **kwargs: Any) -> bool:
        # Placeholder for Figma API call
        print(f"[Figma Output] Updating design with content: {content[:50]}...")
        return True
