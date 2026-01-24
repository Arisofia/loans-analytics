"""LLM Provider - Unified interface for OpenAI and Anthropic.

This module provides a unified interface for interacting with multiple LLM providers,
enabling seamless switching and fallback capabilities for the multi-agent system.
"""

import importlib.util
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

if importlib.util.find_spec("openai") is not None:
    OPENAI_AVAILABLE = True
else:
    OPENAI_AVAILABLE = False


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized LLM response format."""

    content: str
    model: str
    provider: str
    tokens_used: int
    confidence: float = 0.0
    reasoning_steps: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def complete(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Complete a conversation."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        should_create_client = (
            OPENAI_AVAILABLE and self.api_key
        )
        if should_create_client:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def is_available(self) -> bool:
        return OPENAI_AVAILABLE and self.client is not None

    def complete(self, messages: List[Dict], temperature: float = 0.7, **kwargs) -> LLMResponse:
        """Complete using OpenAI API."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider="openai",
                tokens_used=response.usage.total_tokens,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            )
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-haiku-20241022",
    ):
        """
        Initialize AnthropicProvider with API key and model.
        If api_key is not provided, it uses the ANTHROPIC_API_KEY environment variable.
        Sets up the Anthropic client if the library and key are available.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        should_create_client = (
            ANTHROPIC_AVAILABLE and self.api_key
        )
        if should_create_client:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def is_available(self) -> bool:
        return ANTHROPIC_AVAILABLE and self.api_key is not None

    def complete(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Complete using Anthropic API."""
        if not self.is_available():
            raise RuntimeError("Anthropic provider not available")

        # Convert messages to Anthropic format
        system_message = ""
        converted_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                converted_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else None,
                messages=converted_messages,
                **kwargs,
            )

            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                metadata={
                    "stop_reason": response.stop_reason,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )
        except Exception as e:
            logger.error("Anthropic API error: %s", e)
            raise


class LLMManager:
    """Manager for multiple LLM providers with fallback support."""

    def __init__(
        self,
        primary_provider: Literal["openai", "anthropic"] = "openai",
        fallback_enabled: bool = True,
    ):
        self.providers = {}
        self.primary_provider = primary_provider
        self.fallback_enabled = fallback_enabled

        # Initialize providers
        if OPENAI_AVAILABLE:
            self.providers["openai"] = OpenAIProvider()
        if ANTHROPIC_AVAILABLE:
            self.providers["anthropic"] = AnthropicProvider()

        logger.info(
            "Initialized LLM Manager with providers: %s",
            list(self.providers.keys()),
        )

    def complete(
        self, messages: List[Dict], provider: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Complete with automatic fallback."""
        provider_name = provider or self.primary_provider

        openai_error = None
        anthropic_error = None
        if OPENAI_AVAILABLE:
            import openai
            openai_error = getattr(openai.error, "APIError", Exception)
        if ANTHROPIC_AVAILABLE:
            anthropic_error = getattr(__import__("anthropic.error", fromlist=["APIError"]), "APIError", Exception)

        if self._is_provider_available(provider_name):
            try:
                return self._try_provider(
                    provider_name,
                    messages,
                    **kwargs
                )
            except (openai_error, anthropic_error) as e:
                logger.warning("%s failed: %s", provider_name, e)
                if not self.fallback_enabled:
                    raise
            except Exception as e:
                logger.error("Unexpected exception: %s", type(e))
                raise
        if self.fallback_enabled:
            return self._fallback_to_available_providers(provider_name, messages, **kwargs)
        raise RuntimeError("All LLM providers failed or unavailable")

    def _is_provider_available(self, provider_name: str) -> bool:
        return provider_name in self.providers and self.providers[provider_name].is_available()

    def _try_provider(self, provider_name: str, messages: List[Dict], **kwargs) -> LLMResponse:
        provider_obj = self.providers[provider_name]
        return provider_obj.complete(messages, **kwargs)

    def _fallback_to_available_providers(self, primary_name: str, messages: List[Dict], **kwargs) -> LLMResponse:
        openai_error = None
        anthropic_error = None
        if OPENAI_AVAILABLE:
            import openai
            openai_error = getattr(openai.error, "APIError", Exception)
        if ANTHROPIC_AVAILABLE:
            anthropic_error = getattr(__import__("anthropic.error", fromlist=["APIError"]), "APIError", Exception)
        for fallback_name, fallback_provider in self.providers.items():
            if fallback_name != primary_name and fallback_provider.is_available():
                logger.info("Falling back to %s", fallback_name)
                try:
                    return fallback_provider.complete(messages, **kwargs)
                except (openai_error, anthropic_error) as e:
                    logger.warning("%s also failed: %s", fallback_name, e)
                    continue
                except Exception as e:
                    logger.error("Unexpected exception: %s", type(e))
                    raise
        raise RuntimeError("All LLM providers failed or unavailable")

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return [name for name, provider in self.providers.items() if provider.is_available()]
