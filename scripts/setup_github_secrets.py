#!/usr/bin/env python3
"""
Set all required GitHub Actions secrets for Abaco Loans Analytics CI/CD.

Reads secrets from .env.local and pushes them to GitHub via the REST API.

Prerequisites:
    1. .env.local must be fully populated (no <<PASTE_...>> placeholders).
    2. A GitHub Personal Access Token (PAT) with 'repo' scope.
       Create at: https://github.com/settings/tokens/new
       Scopes required: repo (full control of private repositories)

Usage:
    python scripts/setup_github_secrets.py --token <YOUR_GITHUB_PAT>

    OR set GITHUB_PAT in .env.local and run:
    python scripts/setup_github_secrets.py
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ── Bootstrap ────────────────────────────────────────────────
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv  # noqa: E402

    env_local = project_root / ".env.local"
    if env_local.exists():
        load_dotenv(env_local, override=True)
except ImportError:
    # python-dotenv is optional for this script
    pass

REPO = "Arisofia/abaco-loans-analytics"
API_BASE = "https://api.github.com"

# Secrets required by .github/workflows/tests.yml and pr-checks.yml
REQUIRED_SECRETS = {
    "SUPABASE_URL": "SUPABASE_URL",
    "SUPABASE_ANON_KEY": "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY": "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY": "OPENAI_API_KEY",
}

# Secrets useful for production but not strictly required for CI
OPTIONAL_SECRETS = {
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY": "GEMINI_API_KEY",
    "SUPABASE_JWT_SECRET": "SUPABASE_JWT_SECRET",
    "SUPABASE_DATABASE_URL": "SUPABASE_DATABASE_URL",
}


def api_request(url: str, method: str = "GET", data: dict | None = None, token: str = "") -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code} — {body}") from e


def get_public_key(token: str) -> tuple[str, str]:
    url = f"{API_BASE}/repos/{REPO}/actions/secrets/public-key"
    resp = api_request(url, token=token)
    return resp["key_id"], resp["key"]


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypt secret value using libsodium (PyNaCl)."""
    try:
        from nacl import encoding, public  # type: ignore
    except ImportError:
        print("  Installing PyNaCl for secret encryption...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyNaCl", "-q"])
        from nacl import encoding, public  # type: ignore

    public_key = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def set_secret(token: str, key_id: str, pub_key: str, secret_name: str, secret_value: str) -> None:
    encrypted = encrypt_secret(pub_key, secret_value)
    url = f"{API_BASE}/repos/{REPO}/actions/secrets/{secret_name}"
    api_request(
        url, method="PUT", data={"encrypted_value": encrypted, "key_id": key_id}, token=token
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Set GitHub Actions secrets from .env.local")
    parser.add_argument(
        "--token", default=os.environ.get("GITHUB_PAT", ""), help="GitHub PAT with repo scope"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print what would be set without setting it"
    )
    args = parser.parse_args()

    if not args.token:
        print("✗ GitHub PAT required.")
        print("  Create one at: https://github.com/settings/tokens/new")
        print("  Required scope: repo")
        print("  Then run: python scripts/setup_github_secrets.py --token <PAT>")
        sys.exit(1)

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Setting GitHub Actions secrets")
    print(f"  Repository: {REPO}")
    print("=" * 60)

    # Validate secrets from environment
    to_set = {}
    skip = []
    for env_var, secret_name in {**REQUIRED_SECRETS, **OPTIONAL_SECRETS}.items():
        val = os.environ.get(env_var, "")
        if not val or "<<PASTE" in val:
            skip.append((secret_name, env_var))
        else:
            to_set[secret_name] = val

    if skip:
        print("\n  ⚠ Skipped (not configured in .env.local):")
        for s, e in skip:
            print(f"    - {s}  (set {e} in .env.local)")

    if not to_set:
        print("\n  ✗ Nothing to set — populate .env.local first.")
        sys.exit(1)

    if args.dry_run:
        print("\n  Would set:")
        for name in to_set:
            print(f"    ✓ {name}")
        return

    # Fetch repo public key
    try:
        key_id, pub_key = get_public_key(args.token)
        print(f"\n  ✓ Fetched repo public key (key_id={key_id[:8]}...)")
    except RuntimeError as e:
        print(f"  ✗ Could not fetch public key: {e}")
        print("    Check your PAT has 'repo' scope and is not expired.")
        sys.exit(1)

    # Upload secrets
    print("\n  Uploading secrets:")
    success = []
    failed = []
    for secret_name, secret_value in to_set.items():
        try:
            set_secret(args.token, key_id, pub_key, secret_name, secret_value)
            print(f"    ✓ {secret_name}")
            success.append(secret_name)
        except RuntimeError as e:
            print(f"    ✗ {secret_name} — {e}")
            failed.append(secret_name)

    print("\n" + "=" * 60)
    print(f"  Result: {len(success)} set, {len(skip)} skipped, {len(failed)} failed")
    if success:
        print(f"\n  Verify at: https://github.com/{REPO}/settings/secrets/actions")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
