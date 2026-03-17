"""Security test: SQL analytics views should avoid dynamic SQL execution."""

from __future__ import annotations

from pathlib import Path


def test_sql_directory_avoids_dynamic_sql_constructs() -> None:
    """`sql/` assets are expected to stay static to reduce injection risk."""
    sql_root = Path("database/sql")
    assert sql_root.exists(), "Expected sql/ directory to exist"

    blocked_patterns = ("execute ", "prepare ", "do $$", "format(")
    violations: list[str] = []

    for sql_file in sql_root.rglob("*.sql"):
        content = sql_file.read_text(encoding="utf-8", errors="ignore").lower()
        for pattern in blocked_patterns:
            if pattern in content:
                violations.append(f"{sql_file}: contains '{pattern.strip()}'")

    assert not violations, "Dynamic SQL detected in sql/ files:\n" + "\n".join(violations)
