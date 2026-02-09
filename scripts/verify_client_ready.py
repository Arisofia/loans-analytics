#!/usr/bin/env python3
"""Client-readiness verification script. Run all checks."""

import importlib.util
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

results = []
warnings = []


def check(name, ok, detail=""):
    status = PASS if ok else FAIL
    results.append((name, ok))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def check_warn(name, ok, detail=""):
    status = PASS if ok else WARN
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
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True)
            .strip()
        )
    except (subprocess.SubprocessError, OSError):
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
        detail = f"present ({len(v)} chars)" if ok else "MISSING or placeholder"
        check(k, ok, detail)
    for k in optional_keys:
        v = envs.get(k, "")
        ok = bool(v) and "YOUR_" not in v and "PLACEHOLDER" not in v
        detail = f"present ({len(v)} chars)" if ok else "MISSING (optional)"
        check_warn(k, ok, detail)

    # --- 2. DATABASE ---
    print("\n2. DATABASE CONNECTION")
    if importlib.util.find_spec("psycopg") is None:
        check_warn("psycopg", False, "not installed; database checks skipped")
    else:
        import psycopg

        conn = None
        cur = None
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

        except Exception as e:
            # Error classification: connection errors happen before cursor creation
            # If we got far enough to create a cursor, classify as query error
            error_name = "PostgreSQL connect" if conn is None else "PostgreSQL query"
            check(error_name, False, str(e)[:80])
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()

    # --- 3. SUPABASE REST API ---
    print("\n3. SUPABASE REST API")
    supabase_url = envs.get("SUPABASE_URL", "")
    if supabase_url and envs.get("SUPABASE_ANON_KEY"):
        # Validate URL scheme and hostname (SSRF prevention)
        try:
            parsed = urllib.parse.urlparse(supabase_url)
            scheme = parsed.scheme.lower()
            hostname = parsed.hostname or ""
            
            # Check if this is localhost
            is_localhost = hostname in ("localhost", "127.0.0.1", "::1") or hostname.startswith("127.")
            
            # Enforce allowed schemes
            if scheme not in ("http", "https"):
                check("SUPABASE_URL scheme", False, f"unsupported scheme '{scheme}' (only http/https allowed)")
            elif scheme == "http" and not is_localhost:
                check_warn("SUPABASE_URL scheme", False, "http:// for non-localhost (should use https://)")
            else:
                check("SUPABASE_URL scheme", True, f"{scheme}:// for {hostname}")
            
            # Only proceed with request if scheme is valid
            if scheme in ("http", "https"):
                try:
                    req = urllib.request.Request(
                        supabase_url + "/rest/v1/",
                        headers={"apikey": envs["SUPABASE_ANON_KEY"]},
                    )
                    resp = urllib.request.urlopen(req, timeout=10)
                    data = json.loads(resp.read())
                    check("REST API reachability", True, f"{len(data)} endpoints")
                except Exception as e:
                    check("REST API reachability", False, str(e)[:80])
        except Exception as e:
            check("SUPABASE_URL scheme", False, f"invalid URL: {str(e)[:60]}")
    else:
        check_warn("REST API", False, "missing SUPABASE_URL or SUPABASE_ANON_KEY")

    # --- 4. OPENAI API ---
    print("\n4. OPENAI API")
    openai_key = envs.get("OPENAI_API_KEY", "")
    key_valid = openai_key.startswith("sk-") and len(openai_key) > 20
    detail = f"present ({len(openai_key)} chars)" if key_valid else "invalid format"
    check_warn("OpenAI API key format", key_valid, detail)
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
    dsn_ok = "ingest" in dsn
    dsn_detail = f"present ({len(dsn)} chars)" if dsn_ok else "missing or invalid"
    check_warn("Sentry DSN", dsn_ok, dsn_detail)
    otel = envs.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    otel_ok = "ingest" in otel
    otel_detail = f"present ({len(otel)} chars)" if otel_ok else "missing or invalid"
    check_warn("OTEL endpoint", otel_ok, otel_detail)

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
        )
        ok = result.returncode == 0
        if ok:
            detail = "config valid"
        else:
            stderr_raw = result.stderr or ""
            # Sanitize stderr to avoid control characters/newlines breaking formatting
            # and to reduce the chance of leaking sensitive context.
            if stderr_raw:
                # Replace non-printable characters (including newlines) with spaces
                stderr_sanitized = "".join(
                    ch if ch.isprintable() else " " for ch in stderr_raw
                )
                # Collapse all whitespace to single spaces to keep it on one line
                stderr_sanitized = " ".join(stderr_sanitized.split())
            else:
                stderr_sanitized = ""

            if stderr_sanitized:
                stderr_truncated = stderr_sanitized[:200]
                if len(stderr_sanitized) > 200:
                    stderr_truncated += "..."
                detail = f"exit code {result.returncode}; stderr: {stderr_truncated}"
            else:
                detail = f"exit code {result.returncode}"
        check("Pipeline config validation", ok, detail)
    except subprocess.TimeoutExpired as e:
        detail = f"timeout after {e.timeout}s while running pipeline validation"
        check("Pipeline config validation", False, detail[:80])
    except OSError as e:
        msg = e.strerror or str(e)
        check("Pipeline config validation", False, f"OS error: {msg}"[:80])
    except subprocess.SubprocessError as e:
        check("Pipeline config validation", False, str(e)[:80])

    # --- 7. KEY FILES ---
    print("\n7. KEY FILES")
    key_files = [
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
    for f in key_files:
        exists = os.path.exists(f)
        check(f, exists)

    real_data_candidates = []
    raw_dir = "data/raw"
    if os.path.isdir(raw_dir):
        real_data_candidates = [
            path for path in os.listdir(raw_dir) if path.startswith("abaco_real_data_")
        ]
    check(
        "data/raw/abaco_real_data_*.csv",
        len(real_data_candidates) > 0,
        ", ".join(sorted(real_data_candidates)[:3]) if real_data_candidates else "none found",
    )

    # --- SUMMARY ---
    passed_results = sum(1 for _, ok in results if ok)
    failed_results = sum(1 for _, ok in results if not ok)
    passed_warnings = sum(1 for _, ok in warnings if ok)
    failed_warnings = sum(1 for _, ok in warnings if not ok)
    total_passed = passed_results + passed_warnings
    total_failed = failed_results
    total_checks = len(results) + len(warnings)

    print("\n" + "=" * 60)
    print(f"  RESULTS: {total_passed} passed ({passed_results} required, {passed_warnings} optional), "
          f"{total_failed} failed (blocking), {failed_warnings} failed (optional)")
    print(f"  Total checks: {total_checks}")
    if failed_results == 0:
        print(f"  [{PASS}] SYSTEM IS CLIENT-READY")
    else:
        print(f"  [{FAIL}] {failed_results} CHECK(S) NEED ATTENTION")
        for name, ok in results:
            if not ok:
                print(f"    - {name}")
    print("=" * 60)
    return 0 if failed_results == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
