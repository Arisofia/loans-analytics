"""Utility to load secrets and avoid logging them in clear text.
This script demonstrates safe logging and a redaction helper for sensitive values.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger("abaco.scripts.load_secrets")


def redact_dict(
    d: Dict[str, Any],
    redact_keys: tuple = ("secret", "token", "password", "key"),
) -> Dict[str, Any]:
    redacted = {}
    for k, v in d.items():
        if any(sub in k.lower() for sub in redact_keys):
            redacted[k] = "<redacted>"
        else:
            # keep non-sensitive values
            redacted[k] = v
    return redacted


def load_secrets(use_vault_fallback: bool = False) -> Dict[str, Any]:
    # Placeholder for the real secret loading implementation
    # Return a dict with status and optionally secrets (never log them)
    if use_vault_fallback:
        # pretend we found secrets
        return {
            "status": "ok",
            "api_key": "<sensitive>",
            "secret_token": "<sensitive>",
        }
    return {"status": "ok"}


def main() -> int:
    results = load_secrets(use_vault_fallback=True)
    
    # Extract safe, non-sensitive fields with type hints
    # Status can only be: "ok", "error", "unknown" (no sensitive data)
    status: str = results.get("status", "unknown")
    error_obj = results.get("error")
    
    # Log status (guaranteed safe - only contains status enum)
    logger.info("load_secrets completed: status=%s", status)
    
    # Log error type only, never the error message (may contain sensitive context)
    if error_obj:
        logger.error("load_secrets failed: error_type=%s", type(error_obj).__name__)
    
    # Full structure with redaction for debugging only
    safe = redact_dict(results)
    logger.debug("load_secrets payload (redacted)=%s", safe)
    
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
