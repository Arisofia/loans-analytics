#!/usr/bin/env python3
"""Push analytics sections to Supabase Edge Function KV store.

Data sources (in precedence order):
1) Google Sheets CSV export URL via --gsheets-url
2) Pipeline snapshot JSON via --pipeline-json
3) Synthetic fallback payload (default)

Usage:
  python scripts/data/push_to_kv.py
  python scripts/data/push_to_kv.py --project-id <id> --anon-key <key>
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

SECTION_NAMES = [
    "summary",
    "portfolio",
    "risk",
    "collections",
    "treasury",
    "sales",
    "vintage",
    "unit-economics",
    "covenants",
    "executive",
    "investor-room",
    "marketing",
    "ai-decision-center",
]
ALLOWED_URL_SCHEMES = {"http", "https"}


@dataclass
class Config:
    project_id: str
    anon_key: str
    base_path: str = "/functions/v1/make-server-a903c193"

    @property
    def endpoint(self) -> str:
        return f"https://{self.project_id}.supabase.co{self.base_path}/data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Push section payloads to Supabase KV")
    parser.add_argument("--project-id", default=os.getenv("VITE_SUPABASE_PROJECT_ID", ""))
    parser.add_argument("--anon-key", default=os.getenv("VITE_SUPABASE_ANON_KEY", ""))
    parser.add_argument("--gsheets-url", default=os.getenv("GSHEETS_CSV_URL", ""))
    parser.add_argument("--pipeline-json", default=os.getenv("PIPELINE_JSON_PATH", ""))
    parser.add_argument("--timeout", type=int, default=20)
    return parser.parse_args()


def _to_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_allowed_url(url: str) -> bool:
    return urllib.parse.urlparse(url).scheme in ALLOWED_URL_SCHEMES


def _safe_urlopen(url_or_request: str | urllib.request.Request, timeout: int):
    target_url = (
        url_or_request.full_url
        if isinstance(url_or_request, urllib.request.Request)
        else str(url_or_request)
    )
    if not _is_allowed_url(target_url):
        raise ValueError(f"Unsupported URL scheme in '{target_url}'")
    return urllib.request.urlopen(url_or_request, timeout=timeout)


def load_from_pipeline_json(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        return None
    return payload


def load_from_gsheets_csv(url: str, timeout: int) -> dict[str, Any] | None:
    if not url:
        return None

    # Security: Validate URL scheme to prevent file:// or other unexpected protocols (Bandit)
    if not _is_allowed_url(url):
        return None

    try:
        with _safe_urlopen(url, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError):
        return None

    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return None

    outstanding = sum(_to_float(r.get("outstanding", "0"), 0.0) for r in rows)
    active_loans = len(rows)
    par30 = _to_float(rows[0].get("par30", "5.7"), 5.7)

    return {
        "summary": {
            "kpis": {
                "total_outstanding": round(outstanding, 2),
                "active_loans": active_loans,
                "par30": par30,
                "active_borrowers": max(active_loans - 11, 0),
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    }


def synthetic_payload() -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    ppc = 412.4
    ppp = 379.8
    return {
        "summary": {
            "kpis": {
                "total_outstanding": 8_520_000,
                "active_loans": 356,
                "par30": 5.7,
                "expected_loss": 2.4,
            },
            "alerts": [
                {
                    "id": "cov-01",
                    "severity": "warning",
                    "message": "2 covenant breaches in current month",
                },
            ],
            "updated_at": now,
        },
        "portfolio": {
            "metrics": {"aum": 8_520_000, "active_loans": 356, "avg_ticket": 23933.0},
            "concentration": {"top10_share_pct": 19.2, "top20_share_pct": 31.8},
            "updated_at": now,
        },
        "risk": {
            "metrics": {"par30": 5.7, "par60": 3.1, "par90": 1.9, "expected_loss": 2.4},
            "vintage_roll_rate": [{"cohort": "2025-Q4", "roll_30_60": 14.6, "cure_rate": 33.2}],
            "updated_at": now,
        },
        "collections": {
            "metrics": {"collection_rate": 94.8, "contact_rate": 80.4, "promise_to_pay": 61.2},
            "agents": [
                {"name": "Collector A", "efficiency": 0.86},
                {"name": "Collector B", "efficiency": 0.79},
            ],
            "updated_at": now,
        },
        "treasury": {
            "metrics": {"cash_reserve": 2_460_000, "liquidity_ratio": 1.83, "advance_rate": 74.6},
            "updated_at": now,
        },
        "sales": {
            "metrics": {"disbursements_mtd": 2_310_000, "approval_rate": 51.4, "repeat_rate": 34.1},
            "updated_at": now,
        },
        "vintage": {
            "cohorts": [
                {"cohort": "2025-Q2", "mob_3_default_pct": 2.6},
                {"cohort": "2025-Q3", "mob_3_default_pct": 3.0},
                {"cohort": "2025-Q4", "mob_3_default_pct": 3.4},
            ],
            "updated_at": now,
        },
        "unit-economics": {
            "metrics": {
                "ppc": ppc,
                "ppp": ppp,
                "ppc_ppp_gap": round(ppc - ppp, 2),
                "ltv_cac": 4.8,
            },
            "updated_at": now,
        },
        "covenants": {
            "status": "WATCH",
            "breaches_count": 2,
            "breaches": [
                {"name": "Concentration", "threshold": 18.0, "actual": 19.2},
                {"name": "PAR30", "threshold": 5.5, "actual": 5.7},
            ],
            "updated_at": now,
        },
        "executive": {
            "state": "CONTROLLED_RISK",
            "confidence": 0.84,
            "top_actions": [
                "Rebalance delinquent segment pricing",
                "Increase collector allocation for 31-60 DPD",
                "Tighten high-concentration originations",
            ],
            "updated_at": now,
        },
        "investor-room": {
            "scenario_analysis": [
                {"scenario": "base", "par30": 5.7, "cash_coverage": 1.83},
                {"scenario": "stress", "par30": 6.8, "cash_coverage": 1.51},
            ],
            "cohort_table": [{"cohort": "2025-Q4", "origination": 1_920_000, "default_pct": 3.4}],
            "updated_at": now,
        },
        "marketing": {
            "summary": {"cac": 125.0, "ltv": 2357.64, "roi": 1786.11, "avg_ticket": 4366.0},
            "channel_performance": [
                {"channel": "Referidos", "leads": 120, "funded": 52, "cac": 80, "quality": "high"},
                {"channel": "Digital", "leads": 380, "funded": 85, "cac": 150, "quality": "medium"},
                {"channel": "KAM directo", "leads": 95, "funded": 48, "cac": 95, "quality": "high"},
                {"channel": "Alianzas", "leads": 65, "funded": 22, "cac": 180, "quality": "medium"},
            ],
            "segment_performance": [
                {
                    "segment": "transporte",
                    "count": 128,
                    "avg_ticket": 4800,
                    "default_rate": 1.2,
                    "ltv": 2592,
                    "roi": 2140.5,
                },
                {
                    "segment": "comercio",
                    "count": 184,
                    "avg_ticket": 4300,
                    "default_rate": 1.6,
                    "ltv": 2322,
                    "roi": 1894.8,
                },
                {
                    "segment": "servicios",
                    "count": 141,
                    "avg_ticket": 3950,
                    "default_rate": 2.3,
                    "ltv": 2133,
                    "roi": 1650.2,
                },
            ],
            "invisible_primes": {
                "count": 46,
                "description": "Customers with low credit score but strong repayment behavior",
                "avg_dpd": 5.2,
                "avg_ticket": 3056.2,
            },
            "updated_at": now,
        },
        "ai-decision-center": {
            "business_state": "WATCH",
            "confidence": 0.86,
            "agents": [
                {
                    "name": "Risk Agent",
                    "status": "Active",
                    "confidence": 0.91,
                    "task": "Reduce PAR30 and roll-rate migration",
                },
                {
                    "name": "Collections Agent",
                    "status": "Active",
                    "confidence": 0.88,
                    "task": "Lift 31-60 DPD cure rates",
                },
                {
                    "name": "Treasury Agent",
                    "status": "Standby",
                    "confidence": 0.79,
                    "task": "Preserve covenant liquidity buffers",
                },
                {
                    "name": "Compliance Agent",
                    "status": "Alert",
                    "confidence": 0.94,
                    "task": "Resolve covenant watch items",
                },
            ],
            "ranked_actions": [
                {
                    "rank": 1,
                    "action": "Mitigate covenant exposure",
                    "confidence": 0.92,
                    "owner": "Credit Committee",
                },
                {
                    "rank": 2,
                    "action": "Lift cure rates for 31-60 DPD",
                    "confidence": 0.89,
                    "owner": "Collections Lead",
                },
                {
                    "rank": 3,
                    "action": "Improve prime acquisition quality",
                    "confidence": 0.84,
                    "owner": "Growth Lead",
                },
            ],
            "opportunities": [
                {
                    "title": "Cross-sell insured product",
                    "estimated_uplift_pct": round(random.uniform(7.0, 11.0), 2),
                },
                {
                    "title": "Invisible-prime payroll products",
                    "estimated_uplift_pct": round(random.uniform(5.0, 9.0), 2),
                },
            ],
            "updated_at": now,
        },
    }


def merge_payload(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    payload = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(payload.get(key), dict):
            merged = dict(payload[key])
            merged.update(value)
            payload[key] = merged
        else:
            payload[key] = value
    return payload


def put_section(config: Config, section: str, body: Any, timeout: int) -> None:
    url = f"{config.endpoint}/{urllib.parse.quote(section, safe='')}"
    req = urllib.request.Request(
        url=url,
        data=json.dumps(body).encode("utf-8"),
        method="PUT",
        headers={
            "Content-Type": "application/json",
            "apikey": config.anon_key,
            "Authorization": f"Bearer {config.anon_key}",
        },
    )
    # urllib.request.urlopen raises HTTPError for 4xx/5xx responses.
    # We allow the exception to propagate to the caller for error reporting.
    with _safe_urlopen(req, timeout=timeout) as response:
        _ = response.read()


def main() -> int:
    args = parse_args()
    if not args.project_id or not args.anon_key:
        print(
            "Missing Supabase credentials. Set VITE_SUPABASE_PROJECT_ID and VITE_SUPABASE_ANON_KEY."
        )
        return 2

    config = Config(project_id=args.project_id, anon_key=args.anon_key)

    payload = synthetic_payload()
    payload = merge_payload(payload, load_from_pipeline_json(args.pipeline_json) or {})
    payload = merge_payload(payload, load_from_gsheets_csv(args.gsheets_url, args.timeout) or {})

    missing_sections = [name for name in SECTION_NAMES if name not in payload]
    if missing_sections:
        print(f"Payload is missing required sections: {', '.join(missing_sections)}")
        return 3

    pushed = 0
    for section in SECTION_NAMES:
        try:
            put_section(config, section, payload[section], args.timeout)
            pushed += 1
            print(f"[OK] {section}")
        except Exception as error:  # pylint: disable=broad-except
            print(f"[ERROR] {section}: {error}")

    print(f"Completed. Sections pushed: {pushed}/{len(SECTION_NAMES)}")
    return 0 if pushed == len(SECTION_NAMES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
