"""
Pipeline Configuration Management

Centralized configuration loader for the unified pipeline.
Reads from config/pipeline.yml and provides structured access to settings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PipelineConfig:
    """Pipeline configuration container."""

    ingestion: dict[str, Any]
    transformation: dict[str, Any]
    calculation: dict[str, Any]
    output: dict[str, Any]
    external_integrations: dict[str, Any]
    observability: dict[str, Any]

    @classmethod
    def load(cls, config_path: Path | None = None) -> "PipelineConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to pipeline.yml (defaults to config/pipeline.yml)

        Returns:
            PipelineConfig instance
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "pipeline.yml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create config/pipeline.yml with pipeline settings."
            )

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(
            ingestion=config_data.get("ingestion", {}),
            transformation=config_data.get("transformation", {}),
            calculation=config_data.get("calculation", {}),
            output=config_data.get("output", {}),
            external_integrations=config_data.get("external_integrations", {}),
            observability=config_data.get("observability", {}),
        )


def load_business_rules(rules_path: Path | None = None) -> dict[str, Any]:
    """
    Load business rules from YAML file.

    Args:
        rules_path: Path to business_rules.yaml

    Returns:
        Dictionary of business rules
    """
    if rules_path is None:
        rules_path = Path(__file__).parent.parent.parent / "config" / "business_rules.yaml"

    if not rules_path.exists():
        return {}

    with open(rules_path, "r") as f:
        return yaml.safe_load(f)


def load_kpi_definitions(kpi_path: Path | None = None) -> dict[str, Any]:
    """
    Load KPI definitions from YAML file.

    Args:
        kpi_path: Path to kpi_definitions.yaml

    Returns:
        Dictionary of KPI definitions
    """
    if kpi_path is None:
        kpi_path = Path(__file__).parent.parent.parent / "config" / "kpis" / "kpi_definitions.yaml"

    if not kpi_path.exists():
        return {}

    with open(kpi_path, "r") as f:
        return yaml.safe_load(f)
