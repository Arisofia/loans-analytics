"""Utility to load secrets and avoid logging them in clear text.
This script demonstrates safe logging and a redaction helper for sensitive values.
"""
from __future__ import annotations
import logging
from typing import Dict, Any

logger = logging.getLogger("abaco.scripts.load_secrets")


def redact_dict(d: Dict[str, Any], redact_keys: tuple = ("secret", "token", "password", "key")) -> Dict[str, Any]:
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
        return {"status": "ok", "api_key": "<sensitive>", "secret_token": "<sensitive>"}
    return {"status": "ok"}


def main() -> int:
    results = load_secrets(use_vault_fallback=True)

    # Always avoid printing secret values. Log high-level status and a redacted payload if needed.
    status = results.get("status", "unknown")
    logger.info("load_secrets result: status=%s", status)

    if results.get("error"):
        # Log the error safely without echoing any secret values
        logger.error("load_secrets reported an error: %s", str(results.get("error")))

    # If you need to inspect structure for debugging, use a redacted version
    safe = redact_dict(results)
    logger.debug("load_secrets payload (redacted)=%s", safe)

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
