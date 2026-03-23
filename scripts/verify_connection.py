from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import Mapping
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_CANDIDATES = (PROJECT_ROOT / '.env.local', PROJECT_ROOT / '.env')
PLACEHOLDER_MARKERS = ('<<PASTE', 'your-project', 'your-', 'placeholder', 'CHANGE_ME', 'xxxx')
REQUIRED_KEYS = {'SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY', 'OPENAI_API_KEY'}
SUPABASE_REQUIRED = {'SUPABASE_URL': 'Supabase Dashboard -> Settings -> API -> Project URL', 'SUPABASE_ANON_KEY': 'Supabase Dashboard -> Settings -> API -> anon/public key', 'SUPABASE_SERVICE_ROLE_KEY': 'Supabase Dashboard -> Settings -> API -> service_role key'}
SUPABASE_OPTIONAL = {'SUPABASE_PROJECT_REF': 'Project ref slug in the Supabase URL', 'SUPABASE_DATABASE_URL': 'Supabase Dashboard -> Settings -> Database -> Connection string', 'SUPABASE_JWT_SECRET': 'Supabase Dashboard -> Settings -> API -> JWT settings', 'SUPABASE_HISTORICAL_KPI_TABLE': 'Table override, default historical_kpis'}
LLM_REQUIRED = {'OPENAI_API_KEY': 'platform.openai.com -> API keys'}
LLM_OPTIONAL = {'ANTHROPIC_API_KEY': 'console.anthropic.com -> API keys', 'GEMINI_API_KEY': 'aistudio.google.com -> API keys', 'XAI_API_KEY': 'console.x.ai -> API keys'}
GOOGLE_SHEETS = {'GOOGLE_SHEETS_CREDENTIALS_PATH': 'Path to google-service-account.json', 'GOOGLE_SHEETS_SPREADSHEET_ID': 'Google Sheets share URL -> spreadsheet ID'}
SMTP_ALERTS = {'SMTP_HOST': 'SMTP server, for example smtp.gmail.com:587', 'SMTP_USER': 'SMTP username/email', 'SMTP_PASSWORD': 'SMTP password or app password', 'ALERT_EMAIL_FROM': 'Sender address', 'CRITICAL_EMAIL_TO': 'Critical alert recipient'}
API_CONFIG = {'ABACO_API_KEY': 'Internal API authentication secret', 'API_JWT_SECRET': 'JWT secret when API_JWT_ENABLED=1', 'SENTRY_DSN': 'Sentry DSN'}
GITHUB_CI_SECRETS = {'SUPABASE_URL': 'tests.yml uses secrets.SUPABASE_URL', 'SUPABASE_ANON_KEY': 'tests.yml uses secrets.SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY': 'Needed by backend server-side operations', 'OPENAI_API_KEY': 'tests.yml and pr-checks.yml use secrets.OPENAI_API_KEY', 'SNYK_TOKEN': 'security-scan.yml uses secrets.SNYK_TOKEN when configured'}

def load_environment() -> str:
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from dotenv import load_dotenv
    except ImportError:
        print('x python-dotenv not installed - run: pip install python-dotenv')
        raise SystemExit(1)
    for env_path in ENV_CANDIDATES:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return str(env_path)
    print('x No .env.local or .env file found.')
    print('  Run: python scripts/setup_github_secrets.py --init-local')
    raise SystemExit(1)

def print_section(title: str) -> None:
    separator = '=' * 70
    print(f'\n{separator}')
    print(f'  {title}')
    print(separator)

def is_placeholder(value: str) -> bool:
    return any((marker in value for marker in PLACEHOLDER_MARKERS))

def check_group(title: str, entries: Mapping[str, str], *, required: bool) -> tuple[list[str], list[str]]:
    print_section(title)
    bad: list[str] = []
    ok: list[str] = []
    for key, location in entries.items():
        value = os.environ.get(key, '')
        if not value:
            status = 'x MISSING   ' if required else 'o NOT SET   '
            print(f'  {status}{key}')
            print(f'              -> {location}')
            bad.append(key)
            continue
        if is_placeholder(value):
            status = 'x UNFILLED  ' if required else 'o UNFILLED  '
            print(f'  {status}{key}')
            print(f'              -> {location}')
            bad.append(key)
            continue
        print(f'  ok         {key}')
        ok.append(key)
    return (bad, ok)

def validate_google_sheets_file() -> None:
    credentials_path = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_PATH', '')
    if not credentials_path or is_placeholder(credentials_path):
        return
    candidate = Path(credentials_path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    if candidate.exists():
        print(f'  ok SERVICE ACCT FILE exists: {candidate.name}')
        return
    print(f'  x SERVICE ACCT FILE not found: {candidate}')

def print_ci_alignment() -> None:
    print_section('SECTION 7 - GitHub CI secrets alignment check')
    print('  These values must also exist in GitHub Actions secrets.')
    for secret_name, note in GITHUB_CI_SECRETS.items():
        value = os.environ.get(secret_name, '')
        if value and (not is_placeholder(value)):
            print(f'  ok LOCAL     {secret_name}')
            continue
        prefix = 'o NOT SET  ' if secret_name == 'SNYK_TOKEN' else '! MISSING  '
        print(f'  {prefix}{secret_name}')
        print(f'              -> {note}')
    print('  Upload helper: python scripts/setup_github_secrets.py --token <PAT>')

def _describe_supabase_error(error: Exception, key_name: str) -> str:
    message = str(error)
    if 'does not exist' in message:
        return 'Connected, but target table is not migrated yet'
    if '401' in message or 'Invalid API key' in message:
        return f'AUTH FAILED - check {key_name}'
    return message

def ping_supabase_key(label: str, key_name: str, key_value: str, url: str) -> bool:
    try:
        from supabase import create_client
    except ImportError:
        print('  x supabase package not installed - run: pip install supabase')
        raise SystemExit(1)
    try:
        client = create_client(url, key_value)
        response = client.table('kpi_timeseries_daily').select('id').limit(1).execute()
        row_count = len(response.data or [])
        print(f'  ok {label:<13} Connected ({row_count} row(s) returned)')
        return True
    except Exception as error:
        description = _describe_supabase_error(error, key_name)
        print(f'  x  {label:<13} {description}')
        return 'AUTH FAILED' not in description

def run_supabase_checks(*, skip_db_ping: bool, required_missing: list[str]) -> bool:
    print_section('SECTION 8 - Live Supabase connection test')
    if skip_db_ping:
        print('  o Skipped (--no-db-ping)')
        return True
    if required_missing:
        print('  ! Skipping live check until required secrets are fixed.')
        return False
    url = os.environ['SUPABASE_URL']
    anon_key = os.environ['SUPABASE_ANON_KEY']
    service_role_key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    anon_ok = ping_supabase_key('Anon key', 'SUPABASE_ANON_KEY', anon_key, url)
    service_ok = ping_supabase_key('Service role', 'SUPABASE_SERVICE_ROLE_KEY', service_role_key, url)
    return anon_ok and service_ok

def run_openai_check(ping_llm: bool) -> None:
    if not ping_llm:
        return
    print_section('SECTION 9 - OpenAI API connectivity test')
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if not openai_key or is_placeholder(openai_key):
        print('  o Skipped - OPENAI_API_KEY not configured')
        return
    try:
        import httpx
    except ImportError:
        print('  x httpx not installed - run: pip install httpx')
        return
    headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'}
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get('https://api.openai.com/v1/models', headers=headers)
    except Exception as error:
        print(f'  x OpenAI API -> {error}')
        return
    if response.status_code == 200:
        print('  ok OpenAI API -> Reachable and authenticated')
    elif response.status_code == 401:
        print('  x OpenAI API -> Invalid API key (HTTP 401)')
    else:
        print(f'  ! OpenAI API -> HTTP {response.status_code}')

def print_summary(required_bad: list[str], configured_keys: list[str], db_ok: bool) -> None:
    print_section('RESULT')
    required_configured = [key for key in configured_keys if key in REQUIRED_KEYS]
    optional_configured = len(configured_keys) - len(required_configured)
    if required_bad:
        print('  Missing required secrets.')
        for key in required_bad:
            print(f'    - {key}')
        print('  Generate placeholders: python scripts/setup_github_secrets.py --init-local')
        raise SystemExit(1)
    print('  All required secrets are configured.')
    print(f'  Required configured: {len(required_configured)}')
    print(f'  Optional configured: {optional_configured}')
    if db_ok:
        print('  Live Supabase ping succeeded.')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Validate local secrets and live connections')
    parser.add_argument('--ping-llm', action='store_true', help='Also validate OpenAI connectivity')
    parser.add_argument('--no-db-ping', action='store_true', help='Skip live Supabase checks')
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    env_source = load_environment()
    print_section('ABACO LOANS ANALYTICS - Connection Verification')
    print(f'  Env file: {env_source}')
    all_bad: list[str] = []
    all_ok: list[str] = []
    groups = [('SECTION 1 - Core Supabase credentials', SUPABASE_REQUIRED, True), ('SECTION 2 - Extended Supabase settings', SUPABASE_OPTIONAL, False), ('SECTION 3 - Required LLM keys', LLM_REQUIRED, True), ('SECTION 3b - Optional LLM keys', LLM_OPTIONAL, False), ('SECTION 4 - Google Sheets integration', GOOGLE_SHEETS, False), ('SECTION 5 - Monitoring and SMTP alerts', SMTP_ALERTS, False), ('SECTION 6 - API and observability keys', API_CONFIG, False)]
    for title, entries, required in groups:
        bad, ok = check_group(title, entries, required=required)
        if required:
            all_bad.extend(bad)
        all_ok.extend(ok)
        if entries is GOOGLE_SHEETS:
            validate_google_sheets_file()
    print_ci_alignment()
    db_ok = run_supabase_checks(skip_db_ping=args.no_db_ping, required_missing=all_bad)
    run_openai_check(args.ping_llm)
    print_summary(all_bad, all_ok, db_ok)
if __name__ == '__main__':
    main()
