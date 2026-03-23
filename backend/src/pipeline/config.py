from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

def _load_required_yaml_dict(file_path: Path, label: str) -> Dict[str, Any]:
    legacy_message = 'Configuración vacía o malformada. Abortando.'
    try:
        with open(file_path, 'r', encoding='utf-8') as file_handle:
            data = yaml.safe_load(file_handle)
    except yaml.YAMLError as exc:
        raise ValueError(f'{legacy_message} [{label} YAML malformed at {file_path}: {exc}]') from exc
    if data is None:
        raise ValueError(f'{legacy_message} [{label} YAML empty at {file_path}]')
    if not isinstance(data, dict):
        raise ValueError(f'{legacy_message} [{label} YAML must be a mapping at {file_path}]')
    if not data:
        raise ValueError(f'{legacy_message} [{label} YAML contains no keys at {file_path}]')
    return data

@dataclass
class PipelineConfig:
    ingestion: Dict[str, Any]
    transformation: Dict[str, Any]
    calculation: Dict[str, Any]
    output: Dict[str, Any]
    external_integrations: Dict[str, Any]
    observability: Dict[str, Any]

    @classmethod
    def load(cls, config_path: Optional[Path]=None) -> 'PipelineConfig':
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'pipeline.yml'
        if not config_path.exists():
            raise FileNotFoundError(f'Configuration file not found: {config_path}\nPlease create config/pipeline.yml with pipeline settings.')
        config_data = _load_required_yaml_dict(config_path, 'Pipeline configuration')
        required_sections = ('ingestion', 'transformation', 'calculation', 'output', 'external_integrations', 'observability')
        missing_sections = [section for section in required_sections if section not in config_data]
        if missing_sections:
            missing = ', '.join(missing_sections)
            raise ValueError(f'Pipeline configuration missing required sections: {missing}')
        for section in required_sections:
            if not isinstance(config_data[section], dict):
                raise ValueError(f"Pipeline configuration section '{section}' must be a mapping")
        return cls(ingestion=config_data['ingestion'], transformation=config_data['transformation'], calculation=config_data['calculation'], output=config_data['output'], external_integrations=config_data['external_integrations'], observability=config_data['observability'])

def load_business_rules(rules_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load business rules from YAML file.

    Args:
        rules_path: Path to business_rules.yaml

    Returns:
        Dictionary of business rules
    """
    if rules_path is None:
        rules_path = Path(__file__).parent.parent.parent.parent / 'config' / 'business_rules.yaml'
    if not rules_path.exists():
        raise FileNotFoundError(f'Business rules file not found at {rules_path}. Critical business logic depends on this configuration.')
    return _load_required_yaml_dict(rules_path, 'Business rules')

def load_kpi_definitions(kpi_path: Optional[Path]=None) -> Dict[str, Any]:
    if kpi_path is None:
        kpi_path = Path(__file__).parent.parent.parent.parent / 'config' / 'kpis' / 'kpi_definitions.yaml'
    if not kpi_path.exists():
        raise FileNotFoundError(f'KPI definitions file not found at {kpi_path}. Pipeline cannot calculate metrics without valid definitions.')
    return _load_required_yaml_dict(kpi_path, 'KPI definitions')
