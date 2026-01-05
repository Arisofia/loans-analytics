"""Growth agent runtime to score and surface leads for the SDR desk."""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("growth_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RUNS_DIR = Path("data/agents/growth")
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def build_input(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "run_id": args.run_id,
        "date_range": args.date_range,
        "lead_budget": args.lead_budget,
        "query": f"Surface and score leads for the SDR desk with a budget of {args.lead_budget} leads for {args.date_range}.",
    }


def write_result(run_id: str, payload: Dict[str, Any]) -> Path:
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

    orchestrator = AgentOrchestrator()

    agent_config = {
        "name": "GrowthAgent",
        "role": "SDR Lead Specialist",
        "goal": "Score and surface high-quality leads for the SDR desk",
    }

    LOG.info("Executing Growth agent run_id=%s", args.run_id)
    result = orchestrator.run(inputs, agent_config)

    payload = {
        "status": "completed",
        "run_id": args.run_id,
        "lead_budget": args.lead_budget,
        "result": result,
        "launched_at": datetime.utcnow().isoformat() + "Z",
    }

    output_path = write_result(args.run_id, payload)
    LOG.info("Growth agent completed run %s -> %s", args.run_id, output_path)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
