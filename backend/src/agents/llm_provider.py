from __future__ import annotations
import os
from typing import Any, Dict, List, Protocol
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

class LLMProvider(Protocol):

    def complete(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        raise NotImplementedError

class OpenAILLMProvider:

    def __init__(self, model: str | None=None, temperature: float=0.0) -> None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY must be set for OpenAILLMProvider')
        model_name: str = model or os.getenv('OPENAI_MODEL', 'gpt-4o') or 'gpt-4o'
        timeout = float(os.getenv('LLM_TIMEOUT', '60'))
        max_retries = int(os.getenv('LLM_MAX_RETRIES', '2'))
        self._model = ChatOpenAI(model=model_name, temperature=temperature, api_key=SecretStr(api_key), timeout=timeout, max_retries=max_retries)

    def complete(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        response = self._model.invoke(messages, **kwargs)
        return getattr(response, 'content', str(response))
