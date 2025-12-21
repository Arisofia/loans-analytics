"""Client implementations for interacting with external AI providers.

These lightweight wrappers keep network concerns isolated from the business
logic while providing minimal ergonomics for invoking Grok or Gemini models.
"""


import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import google.generativeai as genai
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Normalized response for AI client calls."""

    text: str
    raw: Dict[str, Any]


class GrokClient:
    """Simple HTTP client for Grok/X.ai text generation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "grok-beta", base_url: str = "https://api.groq.com/v1"):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.model = model
        self.base_url = base_url.rstrip("/")
        
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        if not self.api_key:
            raise ValueError("A GROK_API_KEY is required to call the Grok API")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "context": context or {},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.debug("Sending Grok request", extra={"model": self.model})

        response = self.session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return AIResponse(text=text, raw=data)


class GeminiClient:
    """Wrapper around the google-generativeai SDK for Gemini models."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro"):
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("A GOOGLE_API_KEY is required to call Gemini")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        logger.debug("Sending Gemini request", extra={"model": self.model.model_name})
        gen_context = context or {}
        response = self.model.generate_content(prompt, generation_config=gen_context)

        text = getattr(response, "text", None) or "".join(getattr(response, "candidates", []) or [])
        raw = json.loads(response.to_json()) if hasattr(response, "to_json") else {"response": str(response)}
        return AIResponse(text=text, raw=raw)
