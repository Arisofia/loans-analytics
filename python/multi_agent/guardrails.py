"""Guardrails for PII redaction and input/output validation."""

import re
from typing import Any, Dict, List

try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    from pydantic import BaseModel, ValidationError


class Guardrails:
    """Input/output validation and PII redaction."""

    PII_PATTERNS = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
        "ein": re.compile(r"\b\d{2}-\d{7}\b"),
    }

    @classmethod
    def redact_pii(cls, text: str, placeholder: str = "[REDACTED]") -> str:
        """Redact PII from text."""
        redacted = text
        for _, pattern in cls.PII_PATTERNS.items():
            redacted = pattern.sub(placeholder, redacted)
        return redacted

    @classmethod
    def validate_input(cls, data: Dict[str, Any], required_keys: List[str]) -> bool:
        """Validate required keys present."""
        return all(key in data for key in required_keys)

    @classmethod
    def validate_schema(cls, data: Dict[str, Any], schema: type[BaseModel]) -> bool:
        """Validate data against Pydantic schema."""
        try:
            schema(**data)
            return True
        except ValidationError:
            return False

    @classmethod
    def sanitize_context(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context dictionary by redacting PII."""
        sanitized: Dict[str, Any] = {}
        for key, value in context.items():
            if isinstance(value, str):
                sanitized[key] = cls.redact_pii(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_context(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.redact_pii(v) if isinstance(v, str) else v for v in value]
            else:
                sanitized[key] = value
        return sanitized
