"""
Generate structured payload (JSON + Markdown) that Copilot/agents can read to
build dark presentation slides consistent with the ABACO design tokens.
"""

import json
from pathlib import Path

from python.theme import ABACO_THEME

SLIDE_TOPICS = [
    {
        "title": "Portfolio Pulse",
        "headline": "Delinquency & yield balance",
        "body": "Highlight the 3.2% delinquency rate and 16.8% yield, and narrate how automation prevents drift.",
        "metrics": [
            {"label": "Delinquency rate", "value": "3.2%"},
            {"label": "Portfolio yield", "value": "16.8%"},
        ],
        "visual": "growth-path",
    },
    {
        "title": "Growth & Marketing",
        "headline": "Segment capture story",
        "body": "Use the treemap to show weighted principal balances per channel and spotlight under-indexed cohorts.",
        "metrics": [
            {"label": "New loans (current month)", "value": "185"},
            {"label": "Approval uplift", "value": "+18%"},
        ],
        "visual": "sales-treemap",
    },
]


def export_payload(output_dir: Path) -> Path:
    payload = {
        "theme": ABACO_THEME,
        "slides": SLIDE_TOPICS,
        "instructions": [
            "Use the ABACO gradient palette as the background.",
            "Apply Lato for headings and Poppins for callouts.",
            "Embed the growth path and treemap HTML artifacts from exports/presentation/.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "copilot-slide-payload.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


if __name__ == "__main__":
    target = Path("exports/presentation")
    payload_file = export_payload(target)
    print(f"Copilot payload written to {payload_file}")
