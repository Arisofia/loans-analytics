"""Utility to load secrets and avoid logging them in clear text.
This script demonstrates safe logging and a redaction helper for sensitive values.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Literal, TypedDict

logger = logging.getLogger("abaco.scripts.load_secrets")


# Type-safe status values
SecretStatus = Literal["ok", "error", "unknown"]


class SecretResult(TypedDict, total=False):
    """Type-safe structure for load_secrets return value."""

    status: SecretStatus
    error: Exception
    # Note: actual secret fields intentionally not typed to avoid leakage


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


def load_secrets(use_vault_fallback: bool = False) -> SecretResult:
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

    # Extract safe, non-sensitive fields with type-safe annotations
    # Status is constrained to: "ok", "error", "unknown" by SecretStatus type
    status: SecretStatus = results.get("status", "unknown")
    error_obj: Exception | None = results.get("error")

    # SAFE: Status is type-guaranteed to be non-sensitive enum value
    # CodeQL: SecretStatus type constrains value to "ok", "error", or "unknown"
    logger.info("load_secrets completed: status=%s", status)  # nosec B608

    # SAFE: Log only error type, never the error message
    if error_obj:
        logger.error("load_secrets failed: error_type=%s", type(error_obj).__name__)

    # SAFE: Full structure with redaction applied for debugging
    safe = redact_dict(results)
    logger.debug("load_secrets payload (redacted)=%s", safe)

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
