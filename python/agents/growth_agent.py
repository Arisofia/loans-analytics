"""Growth agent runtime to score and surface leads for the SDR desk."""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from python.agents.tools import run_sql_query

LOG = logging.getLogger("growth_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RUNS_DIR = Path("data/agents/growth")
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def build_input(args: argparse.Namespace) -> Dict[str, object]:
    return {
        "run_id": args.run_id,
        "date_range": args.date_range,
        "lead_budget": args.lead_budget,
        "trace": {
            "sql_queries": ["SELECT * FROM analytics.v_loans_overview WHERE days_past_due > 30 LIMIT 5"],
            "data_sources": ["analytics.v_loans_overview", "analytics.kpi_timeseries"],
        },
    }


def write_result(run_id: str, payload: Dict[str, object]) -> Path:
    target = RUNS_DIR / f"growth_agent_{run_id}.json"
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Growth agent harness")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--date-range", default="last_30_days")
    parser.add_argument("--lead-budget", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs = build_input(args)
    sample_query = "SELECT product_id, SUM(balance) AS exposure FROM analytics.v_loans_overview GROUP BY product_id"
    query_result = run_sql_query(sample_query)
    inputs["trace"]["sql_queries"].append(sample_query)
    inputs["trace"]["sample_query_result"] = query_result

    payload = {
        "status": "draft",
        "run_id": args.run_id,
        "lead_budget": args.lead_budget,
        "trace": inputs["trace"],
        "recommendations": [
            {"company": "TBD", "reason": "Placeholder"},
        ],
        "launched_at": datetime.utcnow().isoformat() + "Z",
    }

    output_path = write_result(args.run_id, payload)
    LOG.info("Growth agent created run %s -> %s", args.run_id, output_path)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
