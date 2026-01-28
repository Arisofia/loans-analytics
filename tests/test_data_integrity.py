"""
Test to ensure data integrity and isolation between test and production code.

This test suite enforces Phase B requirements:
1. No production code imports test fixtures
2. Test data only exists in test directories
3. Environment-based data paths are properly configured
"""

import ast
import os
from pathlib import Path
import pytest


def find_python_files(directory: Path, exclude_patterns: list[str]) -> list[Path]:
    """Find all Python files in directory, excluding specified patterns."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Exclude directories matching patterns
        dirs[:] = [d for d in dirs if not any(pattern in str(Path(root) / d) for pattern in exclude_patterns)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if not any(pattern in str(file_path) for pattern in exclude_patterns):
                    python_files.append(file_path)
    
    return python_files


def get_imports_from_file(file_path: Path) -> list[str]:
    """Extract all import statements from a Python file."""
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
                    imports.append(f"{module}.{alias.name}")
        
        return imports
    except (SyntaxError, UnicodeDecodeError):
        # Skip files that can't be parsed
        return []


class TestDataIntegrity:
    """Test suite for data integrity and test/prod isolation."""
    
    def test_no_production_imports_of_fixtures(self):
        """
        Ensure no production code imports test fixtures.
        
        Phase B Requirement: Production code must never import test data.
        """
        project_root = Path(__file__).parent.parent.parent
        python_dir = project_root / "python"
        
        # Exclude test directories and test files
        exclude_patterns = [
            "/tests/",
            "/test_",
            "/testing/",
            "__pycache__",
            ".pyc",
        ]
        
        production_files = find_python_files(python_dir, exclude_patterns)
        
        violations = []
        for file_path in production_files:
            imports = get_imports_from_file(file_path)
            
            # Check for fixture imports
            for imp in imports:
                if 'fixtures' in imp.lower() or 'testing.fixtures' in imp:
                    violations.append({
                        'file': str(file_path.relative_to(project_root)),
                        'import': imp
                    })
        
        assert len(violations) == 0, (
            f"Found {len(violations)} production files importing test fixtures:\n"
            + "\n".join([f"  {v['file']}: {v['import']}" for v in violations])
            + "\n\nProduction code must not import test fixtures."
        )
    
    def test_no_fixtures_in_production_paths(self):
        """
        Ensure fixture files only exist in test directories.
        
        Phase B Requirement: Test data must be isolated in test directories.
        """
        project_root = Path(__file__).parent.parent.parent
        
        # Allowed locations for fixtures
        allowed_dirs = [
            project_root / "tests",
            project_root / "python" / "tests",
        ]
        
        # Find all files with "fixture" in the name
        fixture_files = list(project_root.rglob("*fixture*.py"))
        
        violations = []
        for fixture_file in fixture_files:
            # Skip if in allowed directory or is a cache file
            if any(str(fixture_file).startswith(str(allowed)) for allowed in allowed_dirs):
                continue
            if "__pycache__" in str(fixture_file) or ".pyc" in str(fixture_file):
                continue
            
            violations.append(str(fixture_file.relative_to(project_root)))
        
        assert len(violations) == 0, (
            f"Found {len(violations)} fixture files outside test directories:\n"
            + "\n".join([f"  {v}" for v in violations])
            + "\n\nFixture files must be in tests/ directory only."
        )
    
    def test_environment_config_exists(self):
        """
        Ensure environment configuration is properly set up.
        
        Phase B Requirement: Environment-based data path resolution must exist.
        """
        from python.config import settings
        
        # Verify EnvironmentSettings exists
        assert hasattr(settings, 'environment'), (
            "Settings must have 'environment' attribute for environment-based configuration"
        )
        
        # Verify get_data_root method exists
        assert hasattr(settings.environment, 'get_data_root'), (
            "EnvironmentSettings must have 'get_data_root' method"
        )
        
        # Verify get_test_data_root method exists
        assert hasattr(settings.environment, 'get_test_data_root'), (
            "EnvironmentSettings must have 'get_test_data_root' method"
        )
    
    def test_test_data_root_blocked_in_production(self):
        """
        Ensure test data paths raise error in production environment.
        
        Phase B Requirement: Test data must not be accessible in production.
        """
        from python.config import EnvironmentSettings
        
        # Create a prod environment config
        prod_env = EnvironmentSettings(
            environment="prod",
            prod_data_path="/mnt/prod-data"
        )
        
        # Attempting to get test data root should raise error
        with pytest.raises(RuntimeError, match="not available in production"):
            prod_env.get_test_data_root()
    
    def test_environment_validation(self):
        """
        Ensure environment names are validated.
        
        Phase B Requirement: Only valid environments (dev, staging, prod) allowed.
        """
        from python.config import EnvironmentSettings
        from pydantic import ValidationError
        
        # Valid environments should work
        for env in ["dev", "staging", "prod"]:
            config = EnvironmentSettings(environment=env)
            assert config.environment == env
        
        # Invalid environment should raise error
        with pytest.raises(ValidationError):
            EnvironmentSettings(environment="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
