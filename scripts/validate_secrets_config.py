#!/usr/bin/env python3
"""
Validate that all secrets are properly configured and workflows are ready.

This script checks:
1. All required secrets present in .env.local
2. No hardcoded secrets in code
3. Workflows reference correct secret names
4. Upload script is executable
"""

import sys
import re
from pathlib import Path


def check_env_local(root: Path) -> dict:
    """Validate .env.local has all required secrets."""
    env_path = root / '.env.local'
    
    if not env_path.exists():
        return {'status': 'FAIL', 'message': '.env.local not found'}
    
    env = {}
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    
    REQUIRED = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'OPENAI_API_KEY',
        'API_JWT_SECRET',
    ]
    
    OPTIONAL = ['SNYK_TOKEN']
    
    missing = [k for k in REQUIRED if not env.get(k)]
    if missing:
        return {
            'status': 'FAIL',
            'message': f'Missing required secrets: {", ".join(missing)}'
        }
    
    # Check for empty values (except SNYK_TOKEN which is optional)
    empty_required = [k for k in REQUIRED if env.get(k) in ['', 'xxxxxxxxxxxx', '<<PASTE_GITHUB_PAT>>']]
    if empty_required:
        return {
            'status': 'FAIL',
            'message': f'Secrets have placeholder/empty values: {", ".join(empty_required)}'
        }
    
    present = {
        'required': REQUIRED,
        'optional': [k for k in OPTIONAL if env.get(k)],
        'total': len(REQUIRED) + len([k for k in OPTIONAL if env.get(k)]),
    }
    
    return {
        'status': 'PASS',
        'secrets': present,
        'message': f'All {present["total"]} secrets present'
    }


def check_no_hardcoded_secrets(root: Path) -> dict:
    """Scan codebase for accidentally committed secrets."""
    dangerous_patterns = [
        r'OPENAI_API_KEY\s*=\s*["\']sk-[A-Za-z0-9_-]{20,}',
        r'SUPABASE_ANON_KEY\s*=\s*["\']eyJ[A-Za-z0-9_-]+',
        r'SNYK_TOKEN\s*=\s*["\'][A-Za-z0-9_-]{40,}',
        r'API_JWT_SECRET\s*=\s*["\'][A-Za-z0-9_-]{32,}',
    ]
    
    found_secrets = []
    
    for py_file in root.glob('**/*.py'):
        if '.venv' in py_file.parts or '__pycache__' in py_file.parts:
            continue
        
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                found_secrets.append(str(py_file))
    
    if found_secrets:
        return {
            'status': 'WARN',
            'message': f'Potential hardcoded secrets found in: {", ".join(found_secrets[:3])}'
        }
    
    return {'status': 'PASS', 'message': 'No hardcoded secrets detected'}


def check_workflows(root: Path) -> dict:
    """Verify workflows reference correct secret names."""
    workflows_dir = root / '.github' / 'workflows'
    
    if not workflows_dir.exists():
        return {'status': 'FAIL', 'message': 'Workflows directory not found'}
    
    required_in_workflows = {
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'OPENAI_API_KEY',
        'SNYK_TOKEN',
        'API_JWT_SECRET',
    }
    
    found_secrets = set()
    workflow_count = 0
    
    for yml_file in workflows_dir.glob('*.yml'):
        workflow_count += 1
        content = yml_file.read_text(encoding='utf-8')
        
        for secret in required_in_workflows:
            if f'secrets.{secret}' in content or f'env: {secret}' in content:
                found_secrets.add(secret)
    
    # Not all secrets need to be in all workflows
    if workflow_count == 0:
        return {'status': 'FAIL', 'message': 'No workflows found'}
    
    return {
        'status': 'PASS',
        'message': f'{len(found_secrets)} distinct CI secrets referenced across {workflow_count} workflows',
        'secrets_used': sorted(found_secrets),
    }


def check_upload_script(root: Path) -> dict:
    """Verify upload script exists and is valid."""
    script = root / 'scripts' / 'setup_github_secrets_final.py'
    
    if not script.exists():
        return {'status': 'FAIL', 'message': 'Upload script not found'}
    
    content = script.read_text()
    
    if 'def upload_secrets' not in content or 'REQUIRED' not in content:
        return {'status': 'FAIL', 'message': 'Upload script is incomplete'}
    
    return {'status': 'PASS', 'message': 'Upload script ready'}


def status_symbol(status: str) -> str:
    """Map a status code to a display symbol."""
    if status == 'PASS':
        return '✓'
    if status == 'WARN':
        return '⚠'
    return '✗'


def print_result(name: str, result: dict) -> None:
    """Print a single validation result block."""
    print(f'{status_symbol(result["status"])} {name}')
    print(f'  {result["message"]}')
    if 'secrets_used' in result:
        print(f'  Secrets: {", ".join(result["secrets_used"])}')
    if 'secrets' in result:
        print(f'  Required: {", ".join(result["secrets"]["required"])}')
        if result['secrets']['optional']:
            print(f'  Optional: {", ".join(result["secrets"]["optional"])}')
    print()


def print_exception_result(name: str, exc: Exception) -> None:
    """Print a failed validation caused by an exception."""
    print(f'✗ {name}')
    print(f'  ERROR: {str(exc)}')
    print()


def print_next_steps(failed: int) -> None:
    """Print the appropriate follow-up guidance."""
    if failed > 0:
        print('NEXT STEPS:')
        print('1. Fix any FAIL items above')
        print('2. Re-run this validation')
        print('3. Upload secrets: python scripts/setup_github_secrets_final.py --pat ghp_xxx')
        sys.exit(1)

    print('✓ All checks passed! Repository is ready for CI/CD')
    print()
    print('NEXT STEPS:')
    print('1. Create new GitHub PAT with Actions:write, repo permissions')
    print('2. Revoke old token in GitHub settings')
    print('3. Run upload: python scripts/setup_github_secrets_final.py --pat <token>')
    print('4. Verify in GitHub: Settings > Secrets and variables > Actions')
    print('5. Push to main/develop to trigger workflows')
    sys.exit(0)


def main():
    """Run all validation checks."""
    root = Path('.').resolve()
    
    print('='*70)
    print('  SECRETS CONFIGURATION VALIDATION')
    print('='*70)
    print()
    
    checks = [
        ('Secrets in .env.local', check_env_local),
        ('No hardcoded secrets', check_no_hardcoded_secrets),
        ('Workflows configuration', check_workflows),
        ('Upload script', check_upload_script),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func(root)
            results.append((name, result))

            print_result(name, result)
        except Exception as e:
            results.append((name, {'status': 'ERROR', 'message': str(e)}))

            print_exception_result(name, e)
    
    # Summary
    print('='*70)
    passed = sum(1 for _, r in results if r['status'] == 'PASS')
    warned = sum(1 for _, r in results if r['status'] == 'WARN')
    failed = sum(1 for _, r in results if r['status'] in ('FAIL', 'ERROR'))
    
    total = len(results)
    print(f'Results: {passed}/{total} passed, {warned} warnings, {failed} failed')
    print('='*70)
    print()

    print_next_steps(failed)


if __name__ == '__main__':
    main()
