import os
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Dict

ALLOWED_URL_SCHEMES = {"http", "https"}


def _validate_allowed_url(url: str) -> bool:
    parsed_url = urllib.parse.urlparse(url)
    return parsed_url.scheme in ALLOWED_URL_SCHEMES


def sync_to_supabase(run_dir: Path):
    """
    Syncs pipeline JSON outputs from run_dir to Supabase Edge Function KV store.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL or SUPABASE_ANON_KEY not set.")
        return

    # Base URL for the Edge Function
    base_url = f"{supabase_url}/functions/v1/make-server-a903c193/data"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {supabase_key}"}

    # Mapping of local files to Supabase sections
    mapping = {
        "kpis.json": "summary",
        "segment_kpis.json": "portfolio",  # Simplified mapping
        "risk_alerts.json": "risk",
        "collections.json": "collections",
        "treasury.json": "treasury",
        "sales.json": "sales",
        "vintage_analysis.json": "vintage",
        "unit_economics.json": "unit-economics",
        "covenants.json": "covenants",
    }

    # Also check the decision directory
    decision_dir = run_dir / "decision"
    if decision_dir.exists():
        mapping_decision = {
            "decision_center_state.json": "executive",
        }
        for filename, section in mapping_decision.items():
            file_path = decision_dir / filename
            if file_path.exists():
                _push_file(file_path, section, base_url, headers)

    for filename, section in mapping.items():
        file_path = run_dir / filename
        if file_path.exists():
            _push_file(file_path, section, base_url, headers)


def _push_file(file_path: Path, section: str, base_url: str, headers: Dict[str, str]) -> None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        url = f"{base_url}/{section}"

        # Bandit fix: Audit url open for permitted schemes.
        if not _validate_allowed_url(url):
            parsed_url = urllib.parse.urlparse(url)
            print(f"Error: Unsupported URL scheme {parsed_url.scheme}")
            return

        print(f"Pushing {file_path.name} to {url}...")

        req = urllib.request.Request(
            url=url, data=json.dumps(data).encode("utf-8"), method="PUT", headers=headers
        )

        # Sourcery fix: urlopen raises HTTPError for 4xx/5xx; manual status check is dead code.
        if not _validate_allowed_url(req.full_url):
            print(f"Error: Unsupported URL scheme in request URL {req.full_url}")
            return
        with urllib.request.urlopen(req, timeout=30) as response:  # nosec B310
            # We just need to ensure it completed without exception
            _ = response.read()
            print(f"Successfully synced {section}")

    except urllib.error.HTTPError as e:
        # Catch specific HTTP errors to show details
        print(f"Failed to sync {section}: {e.code} {e.reason}")
        try:
            error_body = e.read().decode()
            if error_body:
                print(f"Response body: {error_body}")
        except (UnicodeDecodeError, OSError, ValueError) as decode_err:
            print(f"Could not decode error body for {section}: {decode_err}")
    except urllib.error.URLError as e:
        print(f"Network error syncing {section}: {e.reason}")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"Error syncing {file_path}: {e}")


if __name__ == "__main__":
    # Example usage: find latest run or pass as arg
    runs_dir = Path("logs/runs")
    if runs_dir.exists():
        runs = sorted(
            [d for d in runs_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if runs:
            latest_run = runs[0]
            print(f"Syncing latest run: {latest_run}")
            sync_to_supabase(latest_run)
        else:
            print("No runs found in logs/runs")
    else:
        print("logs/runs directory not found")
