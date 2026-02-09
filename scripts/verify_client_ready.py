#!/usr/bin/env python3
"""Client-readiness verification script. Run all checks."""

import json
import os
import sys
import urllib.request
from datetime import date

COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_RESET = "\033[0m"
LABEL_PASS = COLOR_GREEN + "PASS" + COLOR_RESET
LABEL_FAIL = COLOR_RED + "FAIL" + COLOR_RESET
LABEL_WARN = COLOR_YELLOW + "WARN" + COLOR_RESET

results = []
warnings = []


def check(name, ok, detail=""):
    status = LABEL_PASS if ok else LABEL_FAIL
    results.append((name, ok))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def check_warn(name, ok, detail=""):
    """Non-blocking check: recorded as warning, does not affect exit code."""
    status = LABEL_PASS if ok else LABEL_WARN
    warnings.append((name, ok))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def load_env():
    envs = {}
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
    if not os.path.exists(env_file):
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    envs[k.strip()] = v.strip().strip('"')
    for k, v in envs.items():
        os.environ[k] = v
    return envs


def main():
    print("=" * 60)
    print("  ABACO LOANS ANALYTICS — CLIENT READINESS CHECK")
    print(f"  Date: {date.today().isoformat()}")
    print("=" * 60)

    envs = load_env()

    # --- 1. CREDENTIALS ---
    print("\n1. CREDENTIALS (.env.local)")
    required_keys = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_PROJECT_REF",
        "DATABASE_URL",
        "OPENAI_API_KEY",
    ]
    optional_keys = [
        "SENTRY_DSN",
        "SENTRY_AUTH_TOKEN",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ]
    for k in required_keys:
        v = envs.get(k, "")
        ok = bool(v) and "YOUR_" not in v and "PLACEHOLDER" not in v
        check(k, ok, f"present ({len(v)} chars)" if ok else "MISSING or placeholder")
    for k in optional_keys:
        v = envs.get(k, "")
        ok = bool(v) and "YOUR_" not in v and "PLACEHOLDER" not in v
        check_warn(k, ok, f"present ({len(v)} chars)" if ok else "MISSING or placeholder")

    # --- 2. DATABASE ---
    print("\n2. DATABASE CONNECTION")
    conn = None
    cur = None
    try:
        import psycopg2

        conn = psycopg2.connect(envs.get("DATABASE_URL", ""), connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        ver = cur.fetchone()[0]
        check("PostgreSQL connect", True, ver[:55])

        cur.execute(
            "SELECT schemaname, count(*) FROM pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog','information_schema') "
            "GROUP BY schemaname ORDER BY schemaname"
        )
        schemas = cur.fetchall()
        for s, c in schemas:
            check(f"Schema '{s}'", True, f"{c} tables")

        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        )
        tables = [r[0] for r in cur.fetchall()]
        check("Public tables", len(tables) > 0, ", ".join(tables[:10]))

        # Check for core tables
        core_tables = ["fact_loans", "kpi_timeseries_daily"]
        for t in core_tables:
            exists = t in tables
            if exists:
                cur.execute(f"SELECT count(*) FROM public.{t}")  # noqa: S608
                cnt = cur.fetchone()[0]
                check(f"Table '{t}'", True, f"{cnt} rows")
            else:
                check(f"Table '{t}'", False, "not found")
    except Exception as e:
        if conn is None:
            check("PostgreSQL connect", False, str(e)[:80])
        else:
            check("PostgreSQL query", False, str(e)[:80])
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                # Ignore cleanup errors to avoid masking primary DB exceptions
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                # Ignore cleanup errors to avoid masking primary DB exceptions
                pass

    # --- 3. SUPABASE REST API ---
    print("\n3. SUPABASE REST API")
    try:
        base_url = envs.get("SUPABASE_URL", "").rstrip("/")
        anon_key = envs.get("SUPABASE_ANON_KEY", "")
        if not base_url.startswith("https://"):
            check("REST API", False, "SUPABASE_URL must use https://")
        else:
            health_table = "monitoring_operational_events"
            url = f"{base_url}/rest/v1/{health_table}?select=id&limit=1"
            req = urllib.request.Request(
                url,
                headers={
                    "apikey": anon_key,
                    "Accept": "application/json",
                },
            )
            resp = urllib.request.urlopen(req, timeout=10)  # noqa: S310 — validated https
            status = resp.getcode()
            check("REST API", 200 <= status < 300, f"HTTP {status} on {health_table}")
    except Exception as e:
        check("REST API", False, str(e)[:80])

    # --- 4. OPENAI API ---
    print("\n4. OPENAI API")
    openai_key = envs.get("OPENAI_API_KEY", "")
    key_valid = openai_key.startswith("sk-") and len(openai_key) > 20
    check_warn("OpenAI API key format", key_valid, f"present ({len(openai_key)} chars)")
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {openai_key}"},
        )
        resp = urllib.request.urlopen(req, timeout=30)  # noqa: S310 — trusted static URL
        models = json.loads(resp.read())
        gpt4 = [m["id"] for m in models["data"] if "gpt-4" in m["id"]]
        check_warn("OpenAI API live", True, f"{len(models['data'])} models, {len(gpt4)} GPT-4")
    except Exception as e:
        check_warn("OpenAI API live", False, str(e)[:80])

    # --- 5. SENTRY ---
    print("\n5. SENTRY / OBSERVABILITY")
    dsn = envs.get("SENTRY_DSN", "")
    check_warn(
        "Sentry DSN",
        bool(dsn) and "ingest" in dsn,
        f"present ({len(dsn)} chars)" if dsn else "MISSING or placeholder",
    )
    otel = envs.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    check_warn(
        "OTEL endpoint",
        bool(otel),
        f"present ({len(otel)} chars)" if otel else "MISSING or placeholder",
    )

    # --- 6. PIPELINE ---
    print("\n6. PIPELINE (dry run)")
    try:
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_data_pipeline.py",
                "--mode",
                "validate",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        check("Pipeline config validation", result.returncode == 0, "config valid")
    except Exception as e:
        check("Pipeline config validation", False, str(e)[:80])

    # --- 7. KEY FILES ---
    print("\n7. KEY FILES")

    core_files = [
        "src/pipeline/orchestrator.py",
        "src/pipeline/ingestion.py",
        "src/pipeline/transformation.py",
        "src/pipeline/calculation.py",
        "src/pipeline/output.py",
        "python/multi_agent/orchestrator.py",
        "python/multi_agent/protocol.py",
        "config/pipeline.yml",
        "config/kpis/kpi_definitions.yaml",
        "config/business_rules.yaml",
        "requirements.txt",
        ".gitignore",
    ]
    for f in core_files:
        exists = os.path.exists(f)
        check(f, exists)

    # Real data file is optional but useful for live runs
    real_data_file = "data/raw/abaco_real_data_20260202.csv"
    exists_real = os.path.exists(real_data_file)
    check_warn(
        real_data_file, exists_real, "present" if exists_real else "optional (not found)"
    )

    # --- SUMMARY ---
    passed_results = sum(1 for _, ok in results if ok)
    failed_results = sum(1 for _, ok in results if not ok)
    passed_warnings = sum(1 for _, ok in warnings if ok)
    failed_warnings = sum(1 for _, ok in warnings if not ok)
    total_passed = passed_results + passed_warnings
    total_checks = len(results) + len(warnings)
    print("\n" + "=" * 60)
    print(
        f"  RESULTS: {total_passed} passed"
        f" ({passed_results} required, {passed_warnings} optional),"
        f" {failed_results} failed (blocking),"
        f" {failed_warnings} failed (optional),"
        f" {total_checks} total"
    )
    if failed_results == 0:
        print(f"  [{LABEL_PASS}] SYSTEM IS CLIENT-READY")
    else:
        print(f"  [{LABEL_FAIL}] {failed_results} BLOCKING CHECK(S) NEED ATTENTION")
        for name, ok in results:
            if not ok:
                print(f"    - {name}")
    print("=" * 60)
    return 0 if failed_results == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
