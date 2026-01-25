import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.paths import Paths
from src.pipeline.utils import deep_merge, load_yaml, resolve_placeholders

logger = logging.getLogger(__name__)


class PipelineConfig:
    """Configuration management with validation, environment overrides, and defaults."""

    DEFAULT_CONFIG_PATH = Paths.config_file()
    ENVIRONMENTS_DIR = Paths.config_file().parent.parent / "environments"

    def __init__(
        self, config_path: Optional[Path] = None, overrides: Optional[Dict[str, Any]] = None
    ):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.environment = os.getenv("PIPELINE_ENV", "development")
        self.config = self._load_config()
        if overrides:
            self.config = deep_merge(self.config, overrides)
            logger.info("Applied runtime configuration overrides")
        self._validate_config()
        logger.info("Pipeline configured for environment: %s", self.environment)

    def _load_config(self) -> Dict[str, Any]:
        """Load base config and merge with environment-specific overrides."""
        if not self.config_path.exists():
            logger.warning("Config file not found: %s, using minimal defaults", self.config_path)
            return self._default_config()

        base_config = load_yaml(str(self.config_path))
        logger.info("Loaded base configuration from %s", self.config_path)

        # Load business rules if they exist
        rules_path = self.config_path.parent / "business_rules.yaml"
        if rules_path.exists():
            base_config["business_rules"] = load_yaml(str(rules_path))
            logger.info("Loaded business rules from %s", rules_path)

        env_config_path = self.ENVIRONMENTS_DIR / f"{self.environment}.yml"
        if env_config_path.exists():
            env_config = load_yaml(str(env_config_path))
            base_config = deep_merge(base_config, env_config)
            logger.info("Merged environment config from %s", env_config_path)
        else:
            logger.warning(
                "Environment config not found: %s, using base config only", env_config_path
            )

        # context: Dict[str, Any] = {}
        return resolve_placeholders(base_config)  # Context ignored for now

    def _default_config(self) -> Dict[str, Any]:
        return {
            "version": "2.0",
            "name": "abaco_unified_pipeline",
            "environment": self.environment,
            "pipeline": {
                "phases": {
                    "ingestion": {},
                    "transformation": {},
                    "calculation": {},
                    "outputs": {},
                }
            },
            "run": {"id_strategy": "timestamp"},
        }

    def _validate_config(self) -> None:
        if "pipeline" not in self.config:
            raise ValueError("Pipeline configuration missing 'pipeline' key")
        if "phases" not in self.config["pipeline"]:
            raise ValueError("Pipeline configuration missing 'phases' key")

    def get(self, *keys: str, default: Any = None) -> Any:
        value: Any = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
