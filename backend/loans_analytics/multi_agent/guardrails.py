import re
from typing import Any, Dict, List
try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    from pydantic import BaseModel, ValidationError

class Guardrails:
    PII_PATTERNS = {'email': re.compile('\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'), 'ssn': re.compile('\\b\\d{3}-\\d{2}-\\d{4}\\b'), 'phone': re.compile('\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b'), 'credit_card': re.compile('\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b'), 'ein': re.compile('\\b\\d{2}-\\d{7}\\b')}

    @classmethod
    def redact_pii(cls, text: str, placeholder: str='[REDACTED]') -> str:
        redacted = text
        for _, pattern in cls.PII_PATTERNS.items():
            redacted = pattern.sub(placeholder, redacted)
        return redacted

    @classmethod
    def validate_input(cls, data: Dict[str, Any], required_keys: List[str]) -> bool:
        return all((key in data for key in required_keys))

    @classmethod
    def validate_schema(cls, data: Dict[str, Any], schema: type[BaseModel]) -> bool:
        try:
            schema(**data)
            return True
        except ValidationError:
            return False

    @classmethod
    def sanitize_for_logging(cls, value: Any, max_length: int=500) -> str:
        text = str(value)
        text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace('\x00', '').replace('\x1b', '')
        text = re.sub('[\\x00-\\x1f\\x7f]', '', text)
        if len(text) > max_length:
            text = f'{text[:max_length]}...[truncated]'
        return text

    @classmethod
    def sanitize_context(cls, context: Dict[str, Any]) -> Dict[str, Any]:
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
