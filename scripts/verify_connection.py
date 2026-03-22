#!/usr/bin/env python3
#!/usr/bin/env python3
"""
verify_connection.py — Abaco Loans Analytics

Validates every secret in .env.local and performs a live ping to Supabase
to confirm authentication. Covers all env var categories used by the project:
  - Core Supabase credentials
  - LLM / AI API keys
  - Google Sheets integration
  - Monitoring / SMTP alerts
  - GitHub CI secrets alignment

Usage:
    python scripts/verify_connection.py
    python scripts/verify_connection.py --ping-llm      # also hit OpenAI API
    python scripts/verify_connection.py --no-db-ping    # skip live DB test
"""

import argparse
import os
import sys
from pathlib import Path

# ── Bootstrap path & dotenv ──────────────────────────────────
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    print("✗ python-dotenv not installed — run: pip install python-dotenv")
    sys.exit(1)

_env_local = project_root / ".env.local"
_env_file = project_root / ".env"
if _env_local.exists():
    load_dotenv(_env_local, override=True)
    _env_source = str(_env_local)
elif _env_file.exists():
    load_dotenv(_env_file, override=True)
    _env_source = str(_env_file)
else:
    print("✗ No .env.local or .env file found.")
    print("  Run: python scripts/setup_github_secrets.py --init-local")
    print("  Then fill in placeholders and re-run this script.")
    sys.exit(1)


# ── Helpers ───────────────────────────────────────────────────
def _mask(val: str) -> str:
    if len(val) > 14:
        return val[:8] + "..." + val[-4:]
    return "***"


def _is_placeholder(val: str) -> bool:
    return any(x in val for x in ("<<PASTE", "your-project", "your-", "placeholder", "CHANGE_ME", "xxxx"))


def _check_group(
    title: str,
    entries: dict[str, str],  # key → where-to-get description
    required: bool = True,
) -> tuple[list[str], list[str]]:
    """Check a group of env vars. Returns (missing_or_placeholder, ok) key lists."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")
    bad: list[str] = []
    ok: list[str] = []
    for key, location in entries.items():
        val = os.environ.get(key, "")
        if not val:
            tag = "✗ MISSING  " if required else "○ NOT SET  "
            print(f"  {tag}{key}")
            print(f"              → {location}")
            bad.append(key)
        elif _is_placeholder(val):
            tag = "✗ UNFILLED " if required else "○ UNFILLED "
            print(f"  {tag}{key}  (still has placeholder text)")
            print(f"              → {location}")
            bad.append(key)
        else:
            print(f"  ✓ OK       {key}")
            ok.append(key)
    return bad, ok


# ─────────────────────────────────────────────────────────────
# Secret definitions — every variable used across the project
# ─────────────────────────────────────────────────────────────

SUPABASE_REQUIRED = {
    "SUPABASE_URL":              "Supabase Dashboard → Settings → API → Project URL",
    "SUPABASE_ANON_KEY":         "Supabase Dashboard → Settings → API → anon / public key",
    "SUPABASE_SERVICE_ROLE_KEY": "Supabase Dashboard → Settings → API → service_role key",
}

SUPABASE_OPTIONAL = {
    "SUPABASE_PROJECT_REF":    "Project ref slug in the URL (e.g. abcxyz123)",
    "SUPABASE_DATABASE_URL":   "Supabase Dashboard → Settings → Database → Connection string",
    "SUPABASE_JWT_SECRET":     "Supabase Dashboard → Settings → API → JWT Settings",
    "SUPABASE_HISTORICAL_KPI_TABLE": "Table name override (default: historical_kpis)",
}

LLM_CI_REQUIRED = {
    "OPENAI_API_KEY": "platform.openai.com → API Keys (required by CI workflows)",
}

LLM_OPTIONAL = {
    "ANTHROPIC_API_KEY": "console.anthropic.com → API Keys",
    "GEMINI_API_KEY":    "aistudio.google.com → API Keys",
    "XAI_API_KEY":       "console.x.ai → API Keys (for Grok)",
}

GOOGLE_SHEETS = {
    "GOOGLE_SHEETS_CREDENTIALS_PATH": "Path to google-service-account.json (see docs/CREDENTIALS_SETUP.md)",
    "GOOGLE_SHEETS_SPREADSHEET_ID":   "Google Sheets → Share → Copy spreadsheet ID from URL",
}

SMTP_ALERTS = {
    "SMTP_HOST":          "SMTP server:port, e.g. smtp.gmail.com:587",
    "SMTP_USER":          "Gmail address used for alerts",
    "SMTP_PASSWORD":      "Gmail App Password (not account password)",
    "ALERT_EMAIL_FROM":   "Sender address (same as SMTP_USER typically)",
    "CRITICAL_EMAIL_TO":  "Recipient address for critical alerts",
}

API_CONFIG = {
    "ABACO_API_KEY":    "Secret key for internal API authentication",
    "API_JWT_SECRET":   "Required only when API_JWT_ENABLED=1",
    "SENTRY_DSN":       "Sentry project DSN (optional — monitoring only)",
}

# GitHub CI secrets derived from actual workflow YAML files
GITHUB_CI_SECRETS = {
    "SUPABASE_URL":          "tests.yml — referenced as \${{ secrets.SUPABASE_URL }}",
    "SUPABASE_ANON_KEY":     "tests.yml — referenced as \${{ secrets.SUPABASE_ANON_KEY }}",
    "SUPABASE_SERVICE_ROLE_KEY": "Pushed by setup_github_secrets.py (not yet in YAML)",
    "OPENAI_API_KEY":        "tests.yml / pr-checks.yml — required by multi-agent tests",
    "SNYK_TOKEN":            "security-scan.yml — optional, Snyk vulnerability scan",
}

# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate .env.local secrets and ping Supabase")
    parser.add_argument("--ping-llm", action="store_true", help="Also test OpenAI API connectivity")
    parser.add_argument("--no-db-ping", action="store_true", help="Skip live Supabase connection test")
    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print("  ABACO LOANS ANALYTICS — Connection Verification")
    print(f"{'=' * 70}")
    print(f"  Env file : {_env_source}")

    all_bad: list[str] = []
    all_ok:  list[str] = []

    # ── Section 1: Core Supabase (required) ───────────────────
    bad, ok = _check_group("SECTION 1 — Core Supabase credentials (REQUIRED)", SUPABASE_REQUIRED, required=True)
    all_bad.extend(bad); all_ok.extend(ok)

    # ── Section 2: Extended Supabase (optional) ───────────────
    bad, ok = _check_group("SECTION 2 — Extended Supabase settings (optional)", SUPABASE_OPTIONAL, required=False)
    all_ok.extend(ok)  # failures here are non-blocking

    # ── Section 3: LLM API keys ───────────────────────────────
    bad, ok = _check_group("SECTION 3 — LLM keys (OPENAI required for CI)", LLM_CI_REQUIRED, required=True)
    all_bad.extend(bad); all_ok.extend(ok)

    bad, ok = _check_group("SECTION 3b — Optional LLM keys", LLM_OPTIONAL, required=False)
    all_ok.extend(ok)

    # ── Section 4: Google Sheets integration ──────────────────
    bad, ok = _check_group("SECTION 4 — Google Sheets integration (optional)", GOOGLE_SHEETS, required=False)
    gs_creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "")
    if gs_creds_path and not _is_placeholder(gs_creds_path):
        creds_file = Path(gs_creds_path)
        if not creds_file.is_absolute():
            creds_file = project_root / creds_file
        if creds_file.exists():
            print(f"  ✓ SERVICE ACCT FILE exists: {creds_file.name}")
        else:
            print(f"  ✗ SERVICE ACCT FILE not found: {creds_file}")
            print("    Create it from GCP Console → IAM → Service Accounts → Keys")
    all_ok.extend(ok)

    # ── Section 5: Monitoring / SMTP ─────────────────────────
    bad, ok = _check_group("SECTION 5 — Monitoring / SMTP alerts (optional)", SMTP_ALERTS, required=False)
    all_ok.extend(ok)

    # ── Section 6: API / observability ───────────────────────
    bad, ok = _check_group("SECTION 6 — API & observability keys (optional)", API_CONFIG, required=False)
    all_ok.extend(ok)

    # ── Section 7: GitHub CI alignment check ─────────────────
    print(f"\n{'=' * 70}")
    print("  SECTION 7 — GitHub CI secrets alignment check")
    print(f"{'=' * 70}")
    print("  (These must also be set in GitHub → Settings → Secrets → Actions)")
    for secret_name, note in GITHUB_CI_SECRETS.items():
        val = os.environ.get(secret_name, "")
        if val and not _is_placeholder(val):
            print(f"  ✓ LOCAL    {secret_name}  (Set)")
        else:
            tag = "○ NOT SET " if secret_name == "SNYK_TOKEN" else "⚠ MISSING "
            print(f"  {tag} {secret_name}")
    print("  Run: python scripts/setup_github_secrets.py --token <PAT>  to upload")

    # ── Section 8: Live Supabase ping ────────────────────────
    print(f"\n{'=' * 70}")
    print("  SECTION 8 — Live Supabase connection test")
    print(f"{'=' * 70}")

    if args.no_db_ping:
        print("  ○ Skipped (--no-db-ping)")
    elif all_bad:
        print("  ⚠ Skipping — fix missing required secrets above first.")
    else:
        try:
            from supabase import Client, create_client
        except ImportError:
            print("  ✗ supabase-py not installed — run: pip install supabase")
            sys.exit(1)

        url = os.environ["SUPABASE_URL"]
        anon_key = os.environ["SUPABASE_ANON_KEY"]
        service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

        # Anon key ping
        try:
            client: Client = create_client(url, anon_key)
            resp = client.table("kpi_timeseries_daily").select("id").limit(1).execute()
            row_note = f"{len(resp.data)} row(s)"
            print(f"  ✓ Anon key      → Connected  ({url})")
            print(f"    kpi_timeseries_daily: {row_note}")
        except Exception as exc:
            err = str(exc)
            if "does not exist" in err:
                print("  ✓ Anon key      → Connected  (table not migrated yet — run migrations)")
            elif "401" in err or "Invalid API key" in err:
                print(f"  ✗ Anon key      → AUTH FAILED — check SUPABASE_ANON_KEY")
                sys.exit(1)
            else:
                print(f"  ✗ Anon key      → {err}")
                sys.exit(1)

        # Service role ping
        try:
            admin: Client = create_client(url, service_key)
            admin.table("kpi_timeseries_daily").select("id").limit(1).execute()
            print("  ✓ Service role  → Admin access confirmed")
        except Exception as exc:
            err = str(exc)
            if "does not exist" in err:
                print("  ✓ Service role  → Admin access confirmed (table not migrated yet)")
            elif "401" in err or "Invalid API key" in err:
                print("  ✗ Service role  → AUTH FAILED — check SUPABASE_SERVICE_ROLE_KEY")
                sys.exit(1)
            else:
                print(f"  ✗ Service role  → {err}")
                sys.exit(1)

    # ── Section 9: Optional OpenAI ping ─────────────────────
    if args.ping_llm:
        print(f"\n{'=' * 70}")
        print("  SECTION 9 — OpenAI API connectivity test (--ping-llm)")
        print(f"{'=' * 70}")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai_key or _is_placeholder(openai_key):
            print("  ○ Skipped — OPENAI_API_KEY not configured")
        else:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                with httpx.Client(timeout=10) as http:
                    r = http.get("https://api.openai.com/v1/models", headers=headers)
                if r.status_code == 200:
                    print("  ✓ OpenAI API    → Reachable and authenticated")
                elif r.status_code == 401:
                    print("  ✗ OpenAI API    → Invalid API key (HTTP 401)")
                else:
                    print(f"  ⚠ OpenAI API    → HTTP {r.status_code}")
            except Exception as exc:
                print(f"  ✗ OpenAI API    → {exc}")

    # ── Final summary ────────────────────────────────────────
    print(f"\n{'=' * 70}")
    required_ok  = [k for k in all_ok  if k in {**SUPABASE_REQUIRED, **LLM_CI_REQUIRED}]
    required_bad = [k for k in all_bad if k in {**SUPABASE_REQUIRED, **LLM_CI_REQUIRED}]

    if not required_bad:
        print("  RESULT: ALL REQUIRED SECRETS OK ✓")
        print(f"  {len(required_ok)} required  |  {len(all_ok) - len(required_ok)} optional configured")
        if not args.no_db_ping and not all_bad:
            print("\n  Next step: python scripts/data/setup_supabase_tables.py")
            print("  Upload CI secrets: python scripts/setup_github_secrets.py --token <PAT>")
    else:
        print("  RESULT: MISSING REQUIRED SECRETS ✗")
        print(f"  {len(required_bad)} required key(s) missing:")
        for k in required_bad:
            print(f"    - {k}")
        print("\n  Fix .env.local then re-run this script.")
        print("  Generate template: python scripts/setup_github_secrets.py --init-local")
        sys.exit(1)
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
