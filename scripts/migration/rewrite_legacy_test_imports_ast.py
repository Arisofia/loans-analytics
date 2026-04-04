from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

LEGACY_PREFIX = "backend.loans_analytics"

# Exact overrides first; only applied when target module exists in backend/src.
EXACT_MODULE_MAP: dict[str, str] = {}

# Modules that have no API-equivalent target yet and must remain legacy.
INCOMPATIBLE_MIGRATIONS = {
    "backend.loans_analytics.kpis.engine",
}

# Prefix migration rules attempted after exact mappings.
PREFIX_RULES = (
    ("backend.loans_analytics.multi_agent.", "backend.src.agents.multi_agent."),
    ("backend.loans_analytics.apps.analytics.api.", "backend.src.analytics.api."),
    ("backend.loans_analytics.models.", "backend.src.models."),
)

MODULE_PATTERN = re.compile(r"backend\.loans_analytics(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+")


@dataclass(frozen=True)
class Replacement:
    start: int
    end: int
    text: str


@dataclass
class FileResult:
    path: str
    changed: bool
    rewritten_modules: dict[str, str]
    unresolved_modules: list[str]


def _offset_map(source: str) -> list[int]:
    starts = [0]
    starts.extend(i + 1 for i, ch in enumerate(source) if ch == "\n")
    return starts


def _to_offset(line_starts: list[int], lineno: int, col: int) -> int:
    return line_starts[lineno - 1] + col


def _node_offsets(source: str, node: ast.AST, line_starts: list[int]) -> tuple[int, int]:
    start = _to_offset(line_starts, node.lineno, node.col_offset)
    end = _to_offset(line_starts, node.end_lineno, node.end_col_offset)
    return (start, end)


def _module_exists(repo_root: Path, dotted_module: str) -> bool:
    rel = dotted_module.replace(".", "/")
    py_file = repo_root / f"{rel}.py"
    pkg_init = repo_root / rel / "__init__.py"
    return py_file.exists() or pkg_init.exists()


def _resolve_module(repo_root: Path, old_module: str) -> str | None:
    if old_module in INCOMPATIBLE_MIGRATIONS:
        return None

    if old_module in EXACT_MODULE_MAP:
        candidate = EXACT_MODULE_MAP[old_module]
        if _module_exists(repo_root, candidate):
            return candidate

    for old_prefix, new_prefix in PREFIX_RULES:
        if old_module.startswith(old_prefix):
            candidate = old_module.replace(old_prefix, new_prefix, 1)
            if _module_exists(repo_root, candidate):
                return candidate

    generic = old_module.replace("backend.loans_analytics.", "backend.src.", 1)
    if generic != old_module and _module_exists(repo_root, generic):
        return generic

    return None


def _format_import_aliases(names: Iterable[ast.alias]) -> str:
    chunks: list[str] = []
    for item in names:
        if item.asname:
            chunks.append(f"{item.name} as {item.asname}")
        else:
            chunks.append(item.name)
    return ", ".join(chunks)


def _rewrite_string_literal(source_segment: str, new_value: str) -> str:
    prefix_match = re.match(r"^([rubfRUBF]*)", source_segment)
    prefix = prefix_match[1] if prefix_match else ""
    stripped = source_segment[len(prefix):]
    quote = "'" if stripped.startswith("'") else "\""
    escaped = new_value.replace("\\", "\\\\")
    if quote == "'":
        escaped = escaped.replace("'", "\\'")
    else:
        escaped = escaped.replace("\"", "\\\"")
    return f"{prefix}{quote}{escaped}{quote}"


def rewrite_file(repo_root: Path, file_path: Path) -> FileResult:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    starts = _offset_map(source)

    replacements: list[Replacement] = []
    rewritten: dict[str, str] = {}
    unresolved: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            changed = False
            new_aliases: list[ast.alias] = []
            for alias in node.names:
                if alias.name.startswith(f"{LEGACY_PREFIX}."):
                    resolved = _resolve_module(repo_root, alias.name)
                    if resolved:
                        rewritten[alias.name] = resolved
                        new_aliases.append(ast.alias(name=resolved, asname=alias.asname))
                        changed = True
                    else:
                        unresolved.add(alias.name)
                        new_aliases.append(alias)
                else:
                    new_aliases.append(alias)
            if changed:
                start, end = _node_offsets(source, node, starts)
                replacements.append(Replacement(start=start, end=end, text=f"import {_format_import_aliases(new_aliases)}"))

        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(f"{LEGACY_PREFIX}."):
                resolved = _resolve_module(repo_root, node.module)
                if resolved:
                    rewritten[node.module] = resolved
                    start, end = _node_offsets(source, node, starts)
                    dots = "." * node.level
                    replacements.append(Replacement(start=start, end=end, text=f"from {dots}{resolved} import {_format_import_aliases(node.names)}"))
                else:
                    unresolved.add(node.module)

        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and LEGACY_PREFIX in node.value:
            original_literal = node.value

            def _replace_match(match: re.Match[str]) -> str:
                old_module = match.group(0)
                resolved = _resolve_module(repo_root, old_module)
                if resolved:
                    rewritten[old_module] = resolved
                    return resolved
                unresolved.add(old_module)
                return old_module

            replaced_literal = MODULE_PATTERN.sub(_replace_match, original_literal)
            if replaced_literal != original_literal:
                start, end = _node_offsets(source, node, starts)
                original_segment = source[start:end]
                replacements.append(
                    Replacement(
                        start=start,
                        end=end,
                        text=_rewrite_string_literal(original_segment, replaced_literal),
                    )
                )

    if not replacements:
        return FileResult(
            path=str(file_path),
            changed=False,
            rewritten_modules={},
            unresolved_modules=sorted(unresolved),
        )

    updated = source
    for item in sorted(replacements, key=lambda x: x.start, reverse=True):
        updated = updated[: item.start] + item.text + updated[item.end :]

    file_path.write_text(updated, encoding="utf-8")
    return FileResult(
        path=str(file_path),
        changed=True,
        rewritten_modules=dict(sorted(rewritten.items())),
        unresolved_modules=sorted(unresolved),
    )


def _default_target_files(repo_root: Path) -> list[Path]:
    tests_dir = repo_root / "backend" / "loans_analytics" / "tests"
    return sorted(p for p in tests_dir.glob("*.py") if p.name != "conftest.py")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite legacy imports in legacy tests using AST.")
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument(
        "--report",
        default="reports/migration/legacy_import_rewrite_report.json",
        help="JSON report output path.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional explicit list of test files to process.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.only:
        files = [repo_root / p for p in args.only]
    else:
        files = _default_target_files(repo_root)

    report_entries: list[dict[str, object]] = []
    changed_files = 0
    total_unresolved = set()

    for file_path in files:
        if not file_path.exists() or file_path.suffix != ".py":
            continue
        result = rewrite_file(repo_root, file_path)
        changed_files += int(result.changed)
        total_unresolved.update(result.unresolved_modules)
        report_entries.append(
            {
                "file": file_path.relative_to(repo_root).as_posix(),
                "changed": result.changed,
                "rewritten_modules": result.rewritten_modules,
                "unresolved_modules": result.unresolved_modules,
            }
        )

    report = {
        "processed_files": len(report_entries),
        "changed_files": changed_files,
        "unchanged_files": len(report_entries) - changed_files,
        "distinct_unresolved_modules": sorted(total_unresolved),
        "entries": report_entries,
    }

    report_path = (repo_root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(json.dumps({
        "processed_files": report["processed_files"],
        "changed_files": report["changed_files"],
        "unresolved_module_count": len(report["distinct_unresolved_modules"]),
        "report": str(report_path),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
