from typing import Any, Optional

class MockLanguageModel:
    """
    A mock language model provider for testing and default initialization.
    """
    def __init__(self, model_name: str = "mock-model", **kwargs: Any):
        self.model_name = model_name

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return f"Mock response for: {prompt[:20]}..."

    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        return f"Mock async response for: {prompt[:20]}..."
