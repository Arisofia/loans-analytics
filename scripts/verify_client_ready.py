#!/usr/bin/env python3
"""Client-readiness verification script. Run all checks."""

import importlib.util
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_RESET = "\033[0m"
LABEL_PASS = COLOR_GREEN + "PASS" + COLOR_RESET
LABEL_FAIL = COLOR_RED + "FAIL" + COLOR_RESET
LABEL_WARN = COLOR_YELLOW + "WARN" + COLOR_RESET

results = []


def check(name, ok, detail=""):
    status = LABEL_PASS if ok else LABEL_FAIL
    results.append((name, ok))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def check_warn(name, ok, detail=""):
    status = LABEL_PASS if ok else LABEL_WARN
    results.append((name, ok))
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
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True)
            .strip()
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        branch = "unknown"

    print("=" * 60)
    print("  ABACO LOANS ANALYTICS — CLIENT READINESS CHECK")
    print(f"  Date: {now} | Branch: {branch}")
    print("=" * 60)

    envs = load_env()

    # --- 1. CREDENTIALS ---
    print("\n1. CREDENTIALS (.env.local)")
    required_keys = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "DATABASE_URL",
    ]
    optional_keys = [
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_PROJECT_REF",
        "OPENAI_API_KEY",
        "SENTRY_DSN",
        "SENTRY_AUTH_TOKEN",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ]
    for k in required_keys:
        v = envs.get(k, "")
        ok = bool(v) and "YOUR_" not in v and "PLACEHOLDER" not in v
        check(k, ok, v[:30] + "..." if ok else "MISSING or placeholder")
    for k in optional_keys:
        v = envs.get(k, "")
        ok = bool(v) and "YOUR_" not in v and "PLACEHOLDER" not in v
        check_warn(k, ok, v[:30] + "..." if ok else "MISSING (optional)")

    # --- 2. DATABASE ---
    print("\n2. DATABASE CONNECTION")
    if importlib.util.find_spec("psycopg") is None:
        check_warn("psycopg", False, "not installed; database checks skipped")
    else:
        try:
            import psycopg
        except (ImportError, OSError) as e:
            check_warn("psycopg", False, f"import failed ({e}); database checks skipped")
        else:
            try:
                conn = psycopg.connect(envs.get("DATABASE_URL", ""), connect_timeout=10)
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
                        cur.execute(f"SELECT count(*) FROM public.{t}")
                        cnt = cur.fetchone()[0]
                        check(f"Table '{t}'", True, f"{cnt} rows")
                    else:
                        check(f"Table '{t}'", False, "not found")

                conn.close()
            except Exception as e:
                check("PostgreSQL connect", False, str(e)[:80])

    # --- 3. SUPABASE REST API ---
    print("\n3. SUPABASE REST API")
    if envs.get("SUPABASE_URL") and envs.get("SUPABASE_ANON_KEY"):
        try:
            base_url = envs["SUPABASE_URL"].rstrip("/")
            anon_key = envs["SUPABASE_ANON_KEY"]
            health_table = "monitoring_operational_events"
            url = f"{base_url}/rest/v1/{health_table}?select=id&limit=1"
            req = urllib.request.Request(
                url,
                headers={
                    "apikey": anon_key,
                    "Accept": "application/json",
                },
            )
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
            check("REST API", 200 <= status < 300, f"HTTP {status} on {health_table}")
        except Exception as e:
            check("REST API", False, str(e)[:80])
    else:
        check_warn("REST API", False, "missing SUPABASE_URL or SUPABASE_ANON_KEY")

    # --- 4. OPENAI API ---
    print("\n4. OPENAI API")
    openai_key = envs.get("OPENAI_API_KEY", "")
    key_valid = openai_key.startswith("sk-") and len(openai_key) > 20
    check_warn("OpenAI API key format", key_valid, openai_key[:20] + "...")
    if key_valid:
        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {openai_key}"},
            )
            resp = urllib.request.urlopen(req, timeout=30)
            models = json.loads(resp.read())
            gpt4 = [m["id"] for m in models["data"] if "gpt-4" in m["id"]]
            check_warn(
                "OpenAI API live", True, f"{len(models['data'])} models, {len(gpt4)} GPT-4"
            )
        except Exception as e:
            check_warn("OpenAI API live", False, str(e)[:80])

    # --- 5. SENTRY ---
    print("\n5. SENTRY / OBSERVABILITY")
    dsn = envs.get("SENTRY_DSN", "")
    check_warn(
        "Sentry DSN",
        bool(dsn) and "ingest" in dsn,
        dsn[:40] + "..." if dsn else "MISSING (optional)",
    )
    otel = envs.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    check_warn(
        "OTEL endpoint",
        bool(otel),
        otel[:50] + "..." if otel else "MISSING (optional)",
    )

    # --- 6. PIPELINE ---
    print("\n6. PIPELINE (dry run)")
    try:
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
        ok = result.returncode == 0
        detail = "config valid" if ok else f"non-zero exit code {result.returncode}"
        check("Pipeline config validation", ok, detail)
    except subprocess.TimeoutExpired as e:
        check(
            "Pipeline config validation",
            False,
            f"pipeline validation timed out after {e.timeout} seconds",
        )
    except OSError as e:
        check(
            "Pipeline config validation",
            False,
            (f"OSError while running pipeline validation: {e.strerror or str(e)}")[:80],
        )
    except subprocess.SubprocessError as e:
        check(
            "Pipeline config validation",
            False,
            (f"Subprocess error during pipeline validation: {str(e)}")[:80],
        )

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
    check(real_data_file, exists_real, "present" if exists_real else "optional (not found)")

    # --- SUMMARY ---
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed, {len(results)} total")
    if failed == 0:
        print(f"  [{LABEL_PASS}] SYSTEM IS CLIENT-READY")
    else:
        print(f"  [{LABEL_FAIL}] {failed} CHECK(S) NEED ATTENTION")
        for name, ok in results:
            if not ok:
                print(f"    - {name}")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
