import json
import logging
import os
from itertools import islice
from pathlib import Path
from typing import Any, Dict, List, Optional

from requests.exceptions import RequestException

from scripts.clients import GrokClient

logger = logging.getLogger(__name__)


class StandaloneAIEngine:
    """Persona-driven AI engine with optional Grok backend."""

    def __init__(
        self,
        knowledge_base_path: Optional[Path] = None,
        ai_client: Optional[GrokClient] = None,
    ) -> None:
        self.personalities: Dict[str, Dict[str, str]] = self._load_personalities()
        self.knowledge_base_path = knowledge_base_path or Path("data/knowledge_base.json")
        self.knowledge_base = self._load_knowledge_base_from_file()
        self.ai_client = ai_client or self._initialize_ai_client()

    def _load_personalities(self) -> Dict[str, Dict[str, str]]:
        return {
            "risk_analyst": {
                "tone": "authoritative and concise",
                "style": "Use bullet points and short paragraphs",
            },
            "portfolio_manager": {
                "tone": "strategic and data-driven",
                "style": "Highlight KPIs, deltas, and portfolio impacts",
            },
            "data_cleanser": {
                "tone": "precise and procedural",
                "style": "Return ordered steps and validation checks",
            },
        }

    def _load_knowledge_base_from_file(self) -> Dict[str, Any]:
        if not self.knowledge_base_path.exists():
            return {}
        with self.knowledge_base_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
            if not isinstance(loaded, dict):
                logger.warning(
                    "Knowledge base at %s is not a dict (type=%s); ignoring",
                    self.knowledge_base_path,
                    type(loaded),
                )
                return {}
            return loaded

    def _initialize_ai_client(self) -> Optional[GrokClient]:
        api_key = os.getenv("GROK_API_KEY")
        return None if not api_key else GrokClient(api_key=api_key)

    def _extract_agent_type(self, agent_id: str) -> str:
        return agent_id.split(":", maxsplit=1)[0].lower()

    def _truncate_content(self, content: str, max_chars: int = 4000) -> str:
        if len(content) <= max_chars:
            return content
        return f"{content[:max_chars]}...[truncated]"

    def _construct_prompt(
        self, personality: Dict[str, str], context: Dict[str, Any], data: Dict[str, Any]
    ) -> str:
        data_payload = self._truncate_content(json.dumps(data, ensure_ascii=False))
        lines: List[str] = [
            f"Tone: {personality.get('tone')}",
            f"Style: {personality.get('style')}",
            f"Context: {context.get('summary', '')}",
            f"Data Points: {data_payload}",
        ]
        knowledge = context.get("knowledge_id")
        if knowledge and knowledge in self.knowledge_base:
            kb_payload = self._truncate_content(
                json.dumps(self.knowledge_base[knowledge], ensure_ascii=False)
            )
            lines.append(f"Knowledge Base: {kb_payload}")
        return "\n".join(lines)

    def generate_response(
        self, agent_id: str, context: Dict[str, Any], data: Dict[str, Any]
    ) -> str:
        agent_type = self._extract_agent_type(agent_id)
        personality = self.personalities.get(agent_type, self.personalities["risk_analyst"])
        prompt = self._construct_prompt(personality, context, data)

        if not self.ai_client:
            return self._offline_response(personality, context, data)

        try:
            response = self.ai_client.generate_text(prompt, context)
            return response.text
        except (RequestException, ValueError) as e:
            logger.warning(f"AI generation failed: {e}")
            return self._offline_response(personality, context, data)

    def _offline_response(
        self, personality: Dict[str, str], context: Dict[str, Any], data: Dict[str, Any]
    ) -> str:
        preview = json.dumps({k: data[k] for k in islice(data, 3)}, ensure_ascii=False)
        return (
            f"[{personality['tone']}] {context.get('summary', 'No summary provided')} | "
            f"Insights based on: {preview}"
        )
