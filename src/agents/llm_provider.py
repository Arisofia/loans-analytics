"""LLM Provider stubs."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Protocol

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


class LLMProvider(Protocol):
    """Protocol for large language model providers used by agents.
    This abstraction allows agents to depend on a narrow, testable interface
    instead of concrete SDKs.
    """

    def complete(self, messages: List[Dict[str, str]], **kwargs: Any) -> str: ...


class OpenAILLMProvider:
    """OpenAI-backed LLM provider using ChatOpenAI.
    Reads configuration from environment variables and exposes a simple
    completion interface for agent workflows.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for OpenAILLMProvider")
        model_name: str = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"

        timeout = float(os.getenv("LLM_TIMEOUT", "60"))
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))

        self._model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=SecretStr(api_key),
            timeout=timeout,
            max_retries=max_retries,
        )

    def complete(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        response = self._model.invoke(messages, **kwargs)
        return getattr(response, "content", str(response))
