from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train scorecard only when required CSV files exist")
    parser.add_argument("--loans", type=Path, default=Path("data/raw/loan_data.csv"))
    parser.add_argument("--payments", type=Path, default=Path("data/raw/real_payment.csv"))
    parser.add_argument("--customers", type=Path, default=Path("data/raw/customer_data.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/scorecard"))
    parser.add_argument("--registry", type=Path, default=Path("models/scorecard/training_registry.jsonl"))
    parser.add_argument("--iv-threshold", type=float, default=0.02)
    parser.add_argument("--cv-folds", type=int, default=5)
    return parser.parse_args()


def _resolve(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _git_commit_hash() -> str:
    git_exe = shutil.which("git") or "git"
    try:
        result = subprocess.run(  # nosec B603
            [git_exe, "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _build_train_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REPO_ROOT / "scripts/ml/train_scorecard.py"),
        "--loans",
        str(_resolve(args.loans)),
        "--payments",
        str(_resolve(args.payments)),
        "--customers",
        str(_resolve(args.customers)),
        "--output-dir",
        str(_resolve(args.output_dir)),
        "--iv-threshold",
        str(args.iv_threshold),
        "--cv-folds",
        str(args.cv_folds),
    ]


def _read_metadata(output_dir: Path) -> dict[str, Any]:
    metadata_path = output_dir / "metadata.json"
    with metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    args = parse_args()

    loans = _resolve(args.loans)
    payments = _resolve(args.payments)
    customers = _resolve(args.customers)
    output_dir = _resolve(args.output_dir)
    registry_path = _resolve(args.registry)

    missing = [str(p) for p in [loans, payments, customers] if not p.exists()]
    if missing:
        print("Skipping training because required CSV files are missing:")
        for item in missing:
            print(f"- {item}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    command = _build_train_command(args)
    print("Running scorecard training...")
    subprocess.run(command, cwd=REPO_ROOT, check=True)  # nosec B603

    metadata = _read_metadata(output_dir)
    metrics = metadata.get("metrics", {})

    run_record: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit_hash(),
        "model_type": metadata.get("model_type", "unknown"),
        "data_files": {
            "loans": str(loans.relative_to(REPO_ROOT)),
            "payments": str(payments.relative_to(REPO_ROOT)),
            "customers": str(customers.relative_to(REPO_ROOT)),
        },
        "metrics": metrics,
    }

    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(run_record) + "\n")

    latest_path = output_dir / "last_training_run.json"
    with latest_path.open("w", encoding="utf-8") as handle:
        json.dump(run_record, handle, indent=2)

    print("Training metadata recorded:")
    print(json.dumps(run_record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
