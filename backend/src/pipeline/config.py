"""
Pipeline Configuration Management

Centralized configuration loader for the unified pipeline.
Reads from config/pipeline.yml and provides structured access to settings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class PipelineConfig:
    """Pipeline configuration container."""

    ingestion: Dict[str, Any]
    transformation: Dict[str, Any]
    calculation: Dict[str, Any]
    output: Dict[str, Any]
    external_integrations: Dict[str, Any]
    observability: Dict[str, Any]

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "PipelineConfig":
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


def load_business_rules(rules_path: Optional[Path] = None) -> Dict[str, Any]:
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
        raise FileNotFoundError(
            f"Business rules file not found at {rules_path}. "
            "Critical business logic depends on this configuration."
        )

    with open(rules_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_kpi_definitions(kpi_path: Optional[Path] = None) -> Dict[str, Any]:
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
        raise FileNotFoundError(
            f"KPI definitions file not found at {kpi_path}. "
            "Pipeline cannot calculate metrics without valid definitions."
        )

    with open(kpi_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
