import logging
import os
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

_UNSAFE_DEFAULTS = {"", "password", "postgres", "admin", "changeme"}


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration and apply environment variable overrides.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing the merged configuration.

    Raises:
        FileNotFoundError: If the config file is not found.
        ValueError: If a required security environment variable is missing
                   or contains an unsafe default.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Configuration YAML malformed: {config_path}: {exc}") from exc

    if config is None:
        raise ValueError(f"Configuration YAML is empty: {config_path}")
    if not isinstance(config, dict):
        raise ValueError(f"Configuration YAML must be a mapping: {config_path}")
    if not config:
        raise ValueError(f"Configuration YAML contains no keys: {config_path}")

    # 1. Supabase credentials
    if "supabase" in config:
        sb_section = config["supabase"]
        env_url = os.getenv("SUPABASE_URL")
        env_key = os.getenv("SUPABASE_ANON_KEY")

        if env_url:
            sb_section["url"] = env_url
        if env_key:
            sb_section["key"] = env_key

        if not sb_section.get("url") or not sb_section.get("key"):
            raise ValueError(
                "Supabase URL/Key must be set in config/pipeline.yml or environment variables."
            )

    # 2. Database credentials (safe defaults check)
    if "database" in config:
        db_section = config["database"]
        env_password = os.getenv("DB_PASSWORD")

        if env_password is not None:
            db_password = env_password
        else:
            raw_password = db_section.get("password")
            if raw_password is None:
                # Treat missing password as empty so it is caught by the unsafe-default check.
                db_password = ""  # nosec
            else:
                db_password = str(raw_password)

        if db_password.lower() in _UNSAFE_DEFAULTS:
            raise ValueError(
                "DB_PASSWORD environment variable not set or contains an unsafe default value."
            )
        db_section["password"] = db_password

    logger.debug("Loaded config from %s", config_path)
    return config
