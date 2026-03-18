from pathlib import Path

import pytest
import yaml

from backend.src.pipeline.config import PipelineConfig, load_business_rules, load_kpi_definitions


def test_pipeline_config_load_not_found():
    """Test loading a non-existent config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        PipelineConfig.load(Path("non_existent.yml"))


def test_pipeline_config_load_valid(tmp_path):
    """Test loading a valid config file."""
    config_data = {
        "ingestion": {"source": "csv"},
        "transformation": {"clean": True},
        "calculation": {"metrics": ["par30"]},
        "output": {"format": "parquet"},
        "external_integrations": {"supabase": True},
        "observability": {"enabled": True},
    }
    config_file = tmp_path / "pipeline.yml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = PipelineConfig.load(config_file)
    assert config.ingestion == {"source": "csv"}
    assert config.transformation == {"clean": True}
    assert config.calculation == {"metrics": ["par30"]}
    assert config.output == {"format": "parquet"}
    assert config.external_integrations == {"supabase": True}
    assert config.observability == {"enabled": True}


def test_load_business_rules_not_found():
    """Test loading non-existent business rules raises FileNotFoundError (fail-fast doctrine)."""
    with pytest.raises(FileNotFoundError):
        load_business_rules(Path("non_existent_rules.yaml"))


def test_load_business_rules_valid(tmp_path):
    """Test loading valid business rules."""
    rules_data = {"rule1": {"threshold": 80}}
    rules_file = tmp_path / "business_rules.yaml"
    with open(rules_file, "w") as f:
        yaml.dump(rules_data, f)

    rules = load_business_rules(rules_file)
    assert rules == rules_data


def test_load_kpi_definitions_not_found():
    """Test loading non-existent KPI definitions raises FileNotFoundError (fail-fast doctrine)."""
    with pytest.raises(FileNotFoundError):
        load_kpi_definitions(Path("non_existent_kpis.yaml"))


def test_load_kpi_definitions_valid(tmp_path):
    """Test loading valid KPI definitions."""
    kpi_data = {"PAR30": {"name": "Portfolio at Risk"}}
    kpi_file = tmp_path / "kpi_definitions.yaml"
    with open(kpi_file, "w") as f:
        yaml.dump(kpi_data, f)

    kpis = load_kpi_definitions(kpi_file)
    assert kpis == kpi_data

