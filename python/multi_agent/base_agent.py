"""Base agent with guardrails, tracing, and LLM integration."""

import os
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from openai import OpenAI
else:
    try:
        from openai import OpenAI
    except ImportError:
        OpenAI = None

from python.logging_config import get_logger

from .guardrails import Guardrails
from .protocol import (
    AgentError,
    AgentRequest,
    AgentResponse,
    AgentRole,
    LLMProvider,
    Message,
    MessageRole,
)
from .tracing import AgentTracer

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base agent with standard protocol, guardrails, and tracing."""

    def __init__(
        self,
        role: AgentRole,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: Optional[str] = None,
        tracer: Optional[AgentTracer] = None,
    ):
        self.role = role
        self.provider = provider
        self.model = model or self._default_model()
        self.tracer = tracer or AgentTracer()
        self.guardrails = Guardrails()
        self._client = self._init_client()

    def _default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            LLMProvider.GEMINI: "gemini-2.0-flash-exp",
        }
        return defaults.get(self.provider, "gpt-4o-mini")

    def _init_client(self) -> Any:
        """Initialize LLM client."""
        initializers = {
            LLMProvider.OPENAI: self._init_openai_client,
            LLMProvider.ANTHROPIC: self._init_anthropic_client,
            LLMProvider.GEMINI: self._init_gemini_client,
        }
        initializer = initializers.get(self.provider)
        if not initializer:
            raise ValueError(f"Unsupported provider: {self.provider}")
        return initializer()

    def _init_openai_client(self) -> Any:
        """Initialize OpenAI client."""
        if not OpenAI:
            raise ImportError("openai package required")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        timeout = float(os.getenv("LLM_TIMEOUT", "60"))
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))

        return OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)

    def _init_anthropic_client(self) -> Any:
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic  # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise ImportError("anthropic package required") from exc

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return Anthropic(api_key=api_key)

    def _init_gemini_client(self) -> Any:
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai  # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise ImportError("google-generativeai package required") from exc

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        return genai

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return agent-specific system prompt."""

    def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request with full guardrails and tracing."""
        span = self.tracer.start_trace(self.role, request)
        self.tracer.log_request(self.role, request)

        start_time = time.time()

        try:
            sanitized_messages = self._sanitize_messages(request.messages)

            system_prompt = self.get_system_prompt()
            context_prompt = self._build_context_prompt(request.context)

            system_content = f"{system_prompt}\n\n{context_prompt}"
            full_messages = [{"role": "system", "content": system_content}]
            full_messages.extend(
                [{"role": msg.role.value, "content": msg.content} for msg in sanitized_messages]
            )

            llm_response = self._call_llm(full_messages, request)
            content = (llm_response.get("content") or "").strip()
            if not content:
                raise ValueError(f"Agent {self.role.value} returned empty content")

            latency_ms = (time.time() - start_time) * 1000

            response = AgentResponse(
                trace_id=request.trace_id,
                agent_role=self.role,
                message=Message(
                    role=MessageRole.ASSISTANT,
                    content=content,
                ),
                context=request.context,
                tokens_used=llm_response.get("tokens_used", 0),
                cost_usd=llm_response.get("cost_usd", 0.0),
                latency_ms=latency_ms,
                provider=self.provider,
                model=self.model,
                finish_reason=llm_response.get("finish_reason"),
                metadata=request.metadata,
            )

            self.tracer.log_response(response)
            self.tracer.end_trace(span, response=response)

            return response

        except Exception as e:
            logger.exception("Agent %s error: %s", self.role.value, e)

            error = AgentError(
                trace_id=request.trace_id,
                agent_role=self.role,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            self.tracer.log_error(error)
            self.tracer.end_trace(span, error=e)

            raise

    def _sanitize_messages(self, messages: List[Message]) -> List[Message]:
        """Sanitize messages for PII."""
        sanitized = []
        for msg in messages:
            sanitized.append(
                Message(
                    role=msg.role,
                    content=self.guardrails.redact_pii(msg.content),
                    timestamp=msg.timestamp,
                    metadata=msg.metadata,
                )
            )
        return sanitized

    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """Build context section for prompt."""
        if not context:
            return ""

        sanitized = self.guardrails.sanitize_context(context)
        lines = ["## Context"]
        for key, value in sanitized.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _call_llm(self, messages: List[Dict[str, str]], request: AgentRequest) -> Dict[str, Any]:
        """Call LLM provider with retry logic for timeout errors."""
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        retry_delays = [1, 2, 4]  # Exponential backoff in seconds

        last_error = None
        for attempt in range(max_retries):
            try:
                if self.provider == LLMProvider.OPENAI:
                    return self._call_openai(messages, request)
                if self.provider == LLMProvider.ANTHROPIC:
                    return self._call_anthropic(messages, request)
                if self.provider == LLMProvider.GEMINI:
                    return self._call_gemini(messages, request)
                raise ValueError(f"Unsupported provider: {self.provider}")
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a timeout or rate limit error
                is_retryable = any(
                    keyword in error_msg
                    for keyword in ["timeout", "timed out", "rate limit", "503", "502", "504"]
                )

                if is_retryable and attempt < max_retries - 1:
                    delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    logger.warning(
                        "LLM call failed (attempt %d/%d): %s. Retrying in %ds...",
                        attempt + 1,
                        max_retries,
                        str(e),
                        delay,
                    )
                    time.sleep(delay)
                    last_error = e
                else:
                    # Not retryable or last attempt
                    raise

        # If we get here, all retries failed
        raise last_error or Exception("LLM call failed after retries")

    def _call_openai(self, messages: List[Dict[str, str]], request: AgentRequest) -> Dict[str, Any]:
        """Call OpenAI API."""
        timeout = float(os.getenv("LLM_TIMEOUT", "60"))

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout=timeout,
        )

        usage = response.usage
        tokens = usage.total_tokens if usage else 0

        cost_per_1k_input = 0.00015
        cost_per_1k_output = 0.0006
        cost = (
            (
                (usage.prompt_tokens * cost_per_1k_input / 1000)
                + (usage.completion_tokens * cost_per_1k_output / 1000)
            )
            if usage
            else 0.0
        )

        return {
            "content": response.choices[0].message.content or "",
            "tokens_used": tokens,
            "cost_usd": cost,
            "finish_reason": response.choices[0].finish_reason,
        }

    def _call_anthropic(
        self, messages: List[Dict[str, str]], request: AgentRequest
    ) -> Dict[str, Any]:
        """Call Anthropic API."""
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]

        timeout = float(os.getenv("LLM_TIMEOUT", "60"))

        response = self._client.messages.create(
            model=self.model,
            system=system_msg,
            messages=user_messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout=timeout,
        )

        tokens = response.usage.input_tokens + response.usage.output_tokens

        cost_per_1k_input = 0.003
        cost_per_1k_output = 0.015
        cost = (response.usage.input_tokens * cost_per_1k_input / 1000) + (
            response.usage.output_tokens * cost_per_1k_output / 1000
        )

        return {
            "content": response.content[0].text,
            "tokens_used": tokens,
            "cost_usd": cost,
            "finish_reason": response.stop_reason,
        }

    def _call_gemini(self, messages: List[Dict[str, str]], request: AgentRequest) -> Dict[str, Any]:
        """Call Gemini API."""

        model = self._client.GenerativeModel(self.model)

        prompt_parts = []
        for msg in messages:
            prompt_parts.append(f"{msg['role'].upper()}: {msg['content']}")
        prompt = "\n\n".join(prompt_parts)

        timeout = int(os.getenv("LLM_TIMEOUT", "60"))

        # Configure request with timeout
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
            request_options={"timeout": timeout},
        )

        tokens = getattr(response, "usage_metadata", None)
        tokens_used = tokens.total_token_count if tokens else 0

        cost_per_1k = 0.0001
        cost = tokens_used * cost_per_1k / 1000

        return {
            "content": response.text,
            "tokens_used": tokens_used,
            "cost_usd": cost,
            "finish_reason": "stop",
        }
