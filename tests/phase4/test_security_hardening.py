import ast
import re
from pathlib import Path

import pytest


def test_env_example_contains_no_real_spreadsheet_id():
    """Real Google Sheets IDs are 44-char base64url strings."""
    env_text = Path(".env.example").read_text()
    pattern = re.compile(r"GOOGLE_SHEETS_SPREADSHEET_ID=([A-Za-z0-9_\-]{44})")
    match = pattern.search(env_text)
    assert match is None, (
        f"Real spreadsheet ID found in .env.example: {match[1] if match else ''}. "
        "Replace with placeholder."
    )


def test_env_example_no_duplicate_supabase_anon_key():
    env_text = Path(".env.example").read_text()
    count = env_text.count("SUPABASE_ANON_KEY=")
    assert count == 1, f"SUPABASE_ANON_KEY defined {count} times in .env.example, expected 1"


def test_env_example_no_supabase_secret_api_key():
    env_text = Path(".env.example").read_text()
    assert "SUPABASE_SECRET_API_KEY" not in env_text, (
        "SUPABASE_SECRET_API_KEY is not a real Supabase credential. Remove it."
    )


def test_pipeline_schedule_no_inline_comment():
    env_text = Path(".env.example").read_text()
    problem_lines = [
        line for line in env_text.splitlines() 
        if line.startswith("PIPELINE_RUN_SCHEDULE=") and "#" in line.split("=", 1)[1]
    ]
    assert not problem_lines, (
        f"Inline comment in PIPELINE_RUN_SCHEDULE will corrupt cron expression: {problem_lines}"
    )


def test_formula_engine_uses_asteval_not_eval():
    """Assert the formula engine source does not contain bare eval() calls."""
    source = Path("backend/loans_analytics/kpis/formula_engine.py").read_text()
    tree = ast.parse(source)
    eval_calls = [
        node for node in ast.walk(tree) 
        if isinstance(node, ast.Call) 
        and isinstance(node.func, ast.Name) 
        and node.func.id == "eval"
    ]
    assert not eval_calls, (
        f"Bare eval() found at lines {[n.lineno for n in eval_calls]} in formula_engine.py. "
        "Use asteval.Interpreter or ast-based evaluation instead."
    )


def test_grafana_default_password_is_placeholder():
    env_text = Path(".env.example").read_text()
    assert "admin123" not in env_text, "Weak password 'admin123' found in .env.example"
    assert "GRAFANA_ADMIN_PASSWORD=admin" not in env_text
