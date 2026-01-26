from __future__ import annotations

from pathlib import Path

PROJECT_MARKERS = ("pyproject.toml", "requirements.txt", ".git", ".github")


def find_project_root(start: Path | None = None) -> Path:
    # Coerce `start` to a Path and resolve to avoid type issues when using the
    # `/` operator with different union types (e.g., `Path | Callable`).
    p = Path(start) if start is not None else Path.cwd()
    p = p.resolve()
    for parent in (p, *p.parents):
        if any((parent / m).exists() for m in PROJECT_MARKERS):
            return parent
    return p  # fallback


def resolve_data_path(rel_path: str) -> Path:
    root = find_project_root()
    return (root / rel_path).resolve()
