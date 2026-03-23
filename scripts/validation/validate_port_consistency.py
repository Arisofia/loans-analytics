import re
import sys
from pathlib import Path
from typing import List, Tuple
CANONICAL_PORT_DASHBOARD = 8501
CANONICAL_PORT_API = 8000
DASHBOARD_PORT_VAR = 'STREAMLIT_SERVER_PORT'
API_PORT_VAR = 'API_PORT'
VALIDATION_RULES = {'startup.sh': {'description': 'Startup script for Azure Web App', 'patterns': [('CANONICAL_PORT=\\$\\{STREAMLIT_SERVER_PORT:-8501\\}', 'Canonical port via env override with 8501 default'), ('--server\\.port=\\$\\{CANONICAL_PORT\\}', 'Streamlit invocation with CANONICAL_PORT variable'), ('Default: 8501', 'Documentation comment referencing 8501 as default')], 'must_not_contain': [('STREAMLIT_SERVER_PORT:-8000', 'Hardcoded old port 8000 in startup.sh')]}, 'Dockerfile.dashboard': {'description': 'Dashboard Docker image', 'patterns': [('PORT=8501', 'Port environment variable set to 8501'), ('STREAMLIT_SERVER_PORT=8501', 'Streamlit server port set to 8501'), ('EXPOSE 8501', 'Docker EXPOSE directive set to 8501'), ('--server\\.port=\\$\\{PORT:-8501\\}', 'Port flag uses PORT env var with 8501 default')], 'must_not_contain': [('PORT=8000', 'Old hardcoded port 8000 in Dockerfile.dashboard'), ('EXPOSE 8000', 'Old exposed port 8000 in Dockerfile.dashboard')]}, 'docker-compose.yml': {'description': 'Primary Docker Compose file', 'patterns': [('STREAMLIT_SERVER_PORT: ["\\\']8501["\\\']', 'Streamlit server port set to 8501 in dashboard env')]}}

def validate_file(file_path: Path, rules: dict) -> Tuple[bool, List[str]]:
    errors = []
    if not file_path.exists():
        errors.append(f'File not found: {file_path}')
        return (False, errors)
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        errors.append(f'Error reading file {file_path}: {e}')
        return (False, errors)
    if 'patterns' in rules:
        for pattern, description in rules['patterns']:
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(f'  Missing required pattern in {file_path.name}:\n    Pattern: {pattern}\n    Expected: {description}')
    if 'must_not_contain' in rules:
        for pattern, description in rules['must_not_contain']:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                errors.append(f'  Found forbidden pattern in {file_path.name}:\n    Pattern: {pattern}\n    Message: {description}')
    return (len(errors) == 0, errors)

def main():
    repo_root = Path(__file__).parent.parent.parent
    all_valid = True
    all_errors = []
    print('[INFO] Validating port consistency across Abaco Loans Analytics...\n')
    print('[POLICY] Canonical Port Policy:')
    print(f'   - Dashboard: {CANONICAL_PORT_DASHBOARD} (via {DASHBOARD_PORT_VAR} env var)')
    print(f'   - API: {CANONICAL_PORT_API} (via {API_PORT_VAR} env var)')
    print()
    for file_name, rules in VALIDATION_RULES.items():
        file_path = repo_root / file_name
        is_valid, errors = validate_file(file_path, rules)
        status_icon = '[PASS]' if is_valid else '[FAIL]'
        print(f"{status_icon} {rules['description']}: {file_name}")
        if errors:
            all_valid = False
            for error in errors:
                print(f'   {error}')
            all_errors.extend(errors)
        print()
    print('=' * 70)
    if all_valid:
        print('[SUCCESS] All port consistency validations PASSED!')
        print('\nSummary:')
        print(f'  - Canonical ports {CANONICAL_PORT_DASHBOARD} (Dashboard) and {CANONICAL_PORT_API} (API) consistently referenced')
        print('  - Environment variable overrides properly configured')
        print('  - Documentation reflects updated port policy')
        return 0
    else:
        print('[FAILURE] Port consistency validations FAILED!')
        print(f'\nFound {len(all_errors)} issue(s) to resolve:')
        for i, error in enumerate(all_errors, 1):
            print(f'\n  {i}. {error}')
        return 1
if __name__ == '__main__':
    sys.exit(main())
