

import json
from typing import Any, Dict, Optional, Union

from scripts.clients import AIResponse, GeminiClient, GrokClient


class StandaloneAIEngine:
    """Routes prompts to the appropriate AI backend with safety controls."""

    def __init__(
        self,
        grok_client: Optional[GrokClient] = None,
        gemini_client: Optional[GeminiClient] = None,
        max_prompt_chars: int = 12000,
    ):
        self.grok_client = grok_client or GrokClient()
        self.gemini_client = gemini_client or GeminiClient()
        self.max_prompt_chars = max_prompt_chars

    def _truncate_payload(self, data: Dict[str, Any]) -> str:
        """Ensure payload length stays within safe limits for LLM inputs."""

        payload = json.dumps(data, default=str)
        if len(payload) > self.max_prompt_chars:
            return payload[: self.max_prompt_chars] + "... [TRUNCATED]"
        return payload

    def _select_client(self, payload: str) -> Union[GrokClient, GeminiClient]:
        """Route to Gemini for larger contexts or Grok for smaller prompts."""

        if len(payload) > self.max_prompt_chars // 2:
            return self.gemini_client
        return self.grok_client

    def generate_response(self, personality: str, context: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Generate a response after sanitizing the payload size."""

        sanitized_payload = self._truncate_payload(data)
        prompt = f"Persona: {personality}\nContext: {context}\nData: {sanitized_payload}"

        client = self._select_client(sanitized_payload)
        result: AIResponse = client.generate_text(prompt, context)
        return result.text
