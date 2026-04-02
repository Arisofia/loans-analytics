import ast
import os
from pathlib import Path
import pytest

def find_python_files(directory: Path, exclude_patterns: list[str]) -> list[Path]:
    python_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not any((pattern in str(Path(root) / d) for pattern in exclude_patterns))]
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if not any((pattern in str(file_path) for pattern in exclude_patterns)):
                    python_files.append(file_path)
    return python_files

def get_imports_from_file(file_path: Path) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f'{module}.{alias.name}')
        return imports
    except (SyntaxError, UnicodeDecodeError):
        return []

class TestDataIntegrity:

    def test_no_production_imports_of_fixtures(self):
        project_root = Path(__file__).parent.parent.parent
        python_dir = project_root / 'python'
        exclude_patterns = ['/tests/', '/test_', '/testing/', '__pycache__', '.pyc']
        production_files = find_python_files(python_dir, exclude_patterns)
        violations = []
        for file_path in production_files:
            imports = get_imports_from_file(file_path)
            for imp in imports:
                if 'fixtures' in imp.lower() or 'testing.fixtures' in imp:
                    violations.append({'file': str(file_path.relative_to(project_root)), 'import': imp})
        assert len(violations) == 0, f'Found {len(violations)} production files importing test fixtures:\n' + '\n'.join([f"  {v['file']}: {v['import']}" for v in violations]) + '\n\nProduction code must not import test fixtures.'

    def test_no_fixtures_in_production_paths(self):
        project_root = Path(__file__).parent.parent.parent
        allowed_dirs = [project_root / 'tests', project_root / 'python' / 'tests']
        fixture_files = []
        for target_dir in ['python', 'src']:
            dir_path = project_root / target_dir
            if not dir_path.exists():
                continue
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if d not in ('node_modules', '.venv', '.git', '__pycache__', '.next', 'tests', 'testing')]
                for file in files:
                    if 'fixture' in file.lower() and file.endswith('.py'):
                        fixture_files.append(Path(root) / file)
        violations = []
        for fixture_file in fixture_files:
            if any((str(fixture_file).startswith(str(allowed)) for allowed in allowed_dirs)):
                continue
            if '__pycache__' in str(fixture_file) or '.pyc' in str(fixture_file):
                continue
            violations.append(str(fixture_file.relative_to(project_root)))
        assert len(violations) == 0, f'Found {len(violations)} fixture files outside test directories:\n' + '\n'.join([f'  {v}' for v in violations]) + '\n\nFixture files must be in tests/ directory only.'

    def test_environment_config_exists(self):
        from backend.loans_analytics.config import settings
        assert hasattr(settings, 'environment'), "Settings must have 'environment' attribute for environment-based configuration"
        assert hasattr(settings.environment, 'get_data_root'), "EnvironmentSettings must have 'get_data_root' method"
        assert hasattr(settings.environment, 'get_test_data_root'), "EnvironmentSettings must have 'get_test_data_root' method"

    def test_test_data_root_blocked_in_production(self):
        from backend.loans_analytics.config import EnvironmentSettings
        prod_env = EnvironmentSettings(environment='prod', prod_data_path='/mnt/prod-data')
        with pytest.raises(RuntimeError, match='not available in production'):
            prod_env.get_test_data_root()

    def test_environment_validation(self):
        from pydantic import ValidationError
        from backend.loans_analytics.config import EnvironmentSettings
        for env in ['dev', 'staging', 'prod']:
            config = EnvironmentSettings(environment=env)
            assert config.environment == env
        with pytest.raises(ValidationError):
            EnvironmentSettings(environment='invalid')
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
