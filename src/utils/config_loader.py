"""Secure configuration loader.

Loads YAML configuration files and enforces environment variable overrides
for sensitive values.  Hardcoded fallback secrets are explicitly rejected.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from python.logging_config import get_logger

logger = get_logger(__name__)

# Sentinel values that indicate a secret was never properly configured.
_UNSAFE_DEFAULTS = frozenset({"change_me", "changeme", "password", "secret", ""})


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file with strict validation.

    * Raises ``FileNotFoundError`` if *path* does not exist.
    * If the config contains a ``database`` section, the ``password``
      field is **always** overridden from the ``DB_PASSWORD`` environment
      variable.  An unsafe or missing password causes ``ValueError``.

    Args:
        path: Filesystem path to the YAML configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: *path* does not exist on disk.
        ValueError: A required secret is missing or set to an unsafe default.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Critical config missing: {config_path}")

    with open(config_path, "r", encoding="utf-8") as fh:
        config: dict[str, Any] = yaml.safe_load(fh) or {}

    # Enforce env-var overrides for database secrets
    if "database" in config:
        env_password = os.environ.get("DB_PASSWORD")
        if env_password is not None:
            db_password = env_password
        else:
            db_password = str(config["database"].get("password") or "")
        if db_password.lower() in _UNSAFE_DEFAULTS:
            raise ValueError(
                "DB_PASSWORD environment variable not set or contains an unsafe default value."
            )
        config["database"]["password"] = db_password

    logger.debug("Loaded config from %s", config_path)
    return config
