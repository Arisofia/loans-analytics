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
    def sanitize_for_logging(cls, value: Any, max_length: int = 500) -> str:
        """
        Sanitize user input for safe logging.
        
        Prevents log injection by:
        1. Converting to string
        2. Escaping newlines and control characters
        3. Truncating excessive length
        4. Removing ANSI escape codes
        
        Security: Complies with OWASP Logging Cheat Sheet
        Reference: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
        
        Args:
            value: User-provided value to sanitize
            max_length: Maximum length before truncation (default: 500)
        
        Returns:
            Safe string suitable for logging
        
        Examples:
            >>> Guardrails.sanitize_for_logging("normal.csv")
            'normal.csv'
            >>> Guardrails.sanitize_for_logging("file.csv\\nFAKE LOG ENTRY")
            'file.csv\\\\nFAKE LOG ENTRY'
        """
        # Convert to string
        text = str(value)
        
        # Escape control characters and newlines
        text = (text
            .replace('\n', '\\n')   # Newline
            .replace('\r', '\\r')   # Carriage return
            .replace('\t', '\\t')   # Tab
            .replace('\x00', '')    # Null byte
            .replace('\x1b', '')    # Escape (ANSI codes)
        )
        
        # Remove other control characters (ASCII 0-31, 127)
        text = re.sub(r'[\x00-\x1f\x7f]', '', text)
        
        # Truncate to prevent log flooding
        if len(text) > max_length:
            text = text[:max_length] + "...[truncated]"
        
        return text

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
