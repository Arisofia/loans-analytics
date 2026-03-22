#!/usr/bin/env python3
"""
Upload secrets from .env.local to GitHub Actions Secrets with proper encryption.

Usage:
    export GITHUB_PAT=ghp_xxxxx  # Your GitHub Personal Access Token
    python scripts/setup_github_secrets_final.py

Requirements:
    - GITHUB_PAT environment variable (or pass via --pat flag)
    - .env.local file in repository root with secrets configured
    - pynacl library installed (pip install pynacl)
"""

import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    from nacl import encoding, public
except ImportError:
    print("ERROR: pynacl not installed. Install with: pip install pynacl")
    sys.exit(1)


def load_env(path: Path) -> dict:
    """Load secrets from .env.local file."""
    data = {}
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        data[key] = value
    return data


def api_call(method: str, url: str, token: str, payload: dict = None) -> tuple[int, dict]:
    """Make authenticated GitHub API call."""
    body = None
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'abaco-secrets-bootstrap',
    }
    
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_text = resp.read().decode('utf-8')
            return resp.status, (json.loads(response_text) if response_text else {})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'HTTP {e.code} {url}\n{error_body[:500]}')


def upload_secrets(env_path: Path, token: str) -> None:
    """Upload all secrets to GitHub Actions encrypted secrets store."""
    
    # Load and validate
    if not env_path.exists():
        raise FileNotFoundError(f'.env.local not found at {env_path}')
    
    print(f'Loading secrets from {env_path}...')
    env = load_env(env_path)
    
    # Define required + optional secrets for CI/CD   
    REQUIRED = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY',
        'OPENAI_API_KEY',
        'API_JWT_SECRET',
    ]
    OPTIONAL = ['SNYK_TOKEN']
    
    # Validate required
    missing = [k for k in REQUIRED if not env.get(k)]
    if missing:
        raise ValueError(f'Missing required secrets in .env.local: {", ".join(missing)}')
    
    # Build list to upload: all required + optional if present
    to_upload = REQUIRED + [k for k in OPTIONAL if env.get(k)]
    
    # Get repository info
    try:
        # Try multiple approaches to get origin
        git_cmd = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Programs', 'Git', 'cmd', 'git.exe'
        )
        origin = os.popen(f'"{git_cmd}" remote get-url origin').read().strip()
    except:
        origin = ''
    
    if not origin:
        raise RuntimeError('Could not determine git origin. Are you in a git repository?')
    
    # Parse owner/repo
    match = re.search(r'github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$', origin)
    if not match:
        raise ValueError(f'Invalid GitHub origin URL: {origin}')
    
    owner, repo = match.group('owner'), match.group('repo')
    print(f'Target: {owner}/{repo}\n')
    
    # Fetch public key for encryption
    print('Fetching repository public key...')
    status, key_data = api_call(
        'GET',
        f'https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key',
        token
    )
    if status != 200:
        raise RuntimeError(f'Failed to fetch public key: {key_data}')
    
    public_key_str = key_data['key']
    key_id = key_data['key_id']
    
    # Create sealed box for encryption
    public_key_obj = public.PublicKey(
        public_key_str.encode('utf-8'),
        encoding.Base64Encoder()
    )
    sealed_box = public.SealedBox(public_key_obj)
    
    # Upload each secret
    print(f'Uploading {len(to_upload)} secrets:\n')
    
    failed = []
    for secret_name in to_upload:
        secret_value = env[secret_name]
        
        # Encrypt
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        
        # Upload
        try:
            api_call(
                'PUT',
                f'https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}',
                token,
                {
                    'encrypted_value': encrypted_b64,
                    'key_id': key_id,
                }
            )
            print(f'  ✓ {secret_name}')
        except Exception as e:
            print(f'  ✗ {secret_name}: {str(e)[:80]}')
            failed.append(secret_name)
    
    # Summary
    print(f'\n{"="*60}')
    uploaded = len(to_upload) - len(failed)
    print(f'Uploaded: {uploaded}/{len(to_upload)} secrets')
    
    if failed:
        print(f'Failed: {", ".join(failed)}')
        sys.exit(1)
    else:
        print('All secrets uploaded successfully!')
        print(f'Repository {owner}/{repo} is ready for CI/CD')


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Upload secrets to GitHub Actions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--pat',
        default=os.environ.get('GITHUB_PAT'),
        help='GitHub Personal Access Token (or set GITHUB_PAT env var)'
    )
    parser.add_argument(
        '--env-file',
        default='.env.local',
        help='Path to .env.local file (default: .env.local)'
    )
    
    args = parser.parse_args()
    
    if not args.pat:
        print('ERROR: GITHUB_PAT not provided')
        print('Usage:')
        print('  export GITHUB_PAT=ghp_xxxxx')
        print('  python scripts/setup_github_secrets_final.py')
        print('\nOr:')
        print('  python scripts/setup_github_secrets_final.py --pat ghp_xxxxx')
        sys.exit(1)
    
    env_file = Path(args.env_file)
    
    try:
        upload_secrets(env_file, args.pat)
    except Exception as e:
        print(f'\nERROR: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
