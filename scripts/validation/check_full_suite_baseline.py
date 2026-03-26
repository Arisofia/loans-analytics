from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_summary(report: dict[str, Any]) -> dict[str, int]:
    summary = report.get("summary", {})
    return {
        "collected": _to_int(summary.get("collected", summary.get("total", 0))),
        "passed": _to_int(summary.get("passed", 0)),
        "failed": _to_int(summary.get("failed", 0)),
        "errors": _to_int(summary.get("error", summary.get("errors", 0))),
        "skipped": _to_int(summary.get("skipped", 0)),
        "xfailed": _to_int(summary.get("xfailed", 0)),
        "xpassed": _to_int(summary.get("xpassed", 0)),
    }


def _compare(expected: dict[str, int], actual: dict[str, int]) -> list[str]:
    keys = sorted(set(expected) | set(actual))
    diffs: list[str] = []
    for key in keys:
        if _to_int(expected.get(key, 0)) != _to_int(actual.get(key, 0)):
            diffs.append(f"{key}: expected={expected.get(key, 0)} actual={actual.get(key, 0)}")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pytest full-suite baseline against JSON report")
    parser.add_argument("--baseline", type=Path, required=True, help="Path to expected baseline JSON")
    parser.add_argument("--report", type=Path, required=True, help="Path to pytest JSON report")
    args = parser.parse_args()

    if not args.baseline.exists():
        print(f"Baseline file not found: {args.baseline}")
        return 2
    if not args.report.exists():
        print(f"Report file not found: {args.report}")
        return 2

    baseline = _load_json(args.baseline)
    report = _load_json(args.report)

    expected = {
        "collected": _to_int(baseline.get("collected", 0)),
        "passed": _to_int(baseline.get("passed", 0)),
        "failed": _to_int(baseline.get("failed", 0)),
        "errors": _to_int(baseline.get("errors", 0)),
        "skipped": _to_int(baseline.get("skipped", 0)),
        "xfailed": _to_int(baseline.get("xfailed", 0)),
        "xpassed": _to_int(baseline.get("xpassed", 0)),
    }
    actual = _extract_summary(report)

    diffs = _compare(expected, actual)
    if diffs:
        print("Full-suite baseline mismatch detected:")
        for diff in diffs:
            print(f"- {diff}")
        return 1

    print("Full-suite baseline check passed.")
    print(json.dumps(actual, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
