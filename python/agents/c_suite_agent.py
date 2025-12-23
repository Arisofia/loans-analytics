"""Runtime harness to kick off the C-suite agent workflow."""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

from python.agents.orchestrator import AgentOrchestrator
from python.agents.tools import run_sql_query

LOG = logging.getLogger("c_suite_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RUNS_DIR = Path("data/agents/c_suite")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

SPEC_PATH = Path("agents/specs/c_suite_agent.yaml")
PROMPT_PATH = Path("agents/prompts/c_suite_prompt.md")


def load_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError("C-suite agent prompt missing") from exc


def build_input_data(args: argparse.Namespace, prompt: str) -> Dict[str, object]:
    required_kpis = args.required_kpis or ["PD", "LGD", "EAD", "Liquidity Velocity Index (LVI)", "NPL ratio", "Roll Rates"]
    return {
        "run_id": args.run_id,
        "date_range": args.date_range,
        "required_kpis": required_kpis,
        "top_n_risks": args.top_risks,
        "prompt": prompt,
        "trace": {
            "sql_queries": ["SELECT * FROM analytics.v_loans_overview LIMIT 1"],
            "data_sources": ["analytics.v_loans_overview", "analytics.kpi_timeseries_pd_lgd_ead"],
        },
    }


def write_output(run_id: str, payload: Dict[str, object]) -> Path:
    target = RUNS_DIR / f"c_suite_agent_{run_id}.json"
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="C-suite agent execution harness")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--date-range", required=True)
    parser.add_argument("--required-kpis", nargs="*", help="List of KPIs to include")
    parser.add_argument("--top-risks", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt = load_prompt(PROMPT_PATH)
    input_data = build_input_data(args, prompt)

    try:
        orchestrator = AgentOrchestrator(str(SPEC_PATH))
    except Exception as exc:
        LOG.error("Failed to initialize agent orchestrator: %s", exc)
        raise

    LOG.info("Executing C-suite agent run_id=%s", args.run_id)
    # Demonstrate tool usage in trace
    sample_query = "SELECT * FROM analytics.v_loans_overview LIMIT 5"
    query_result = run_sql_query(sample_query)
    input_data["trace"]["sql_queries"].append(sample_query)
    input_data["trace"]["sample_query_result"] = query_result

    result = orchestrator.run(input_data)
    output = {
        "input": input_data,
        "result": result,
    }
    output_path = write_output(args.run_id, output)
    LOG.info("C-suite agent completed run_id=%s output=%s", args.run_id, output_path)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
