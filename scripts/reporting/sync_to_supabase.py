import os
import json
import requests
from pathlib import Path
from typing import Dict, Any

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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {supabase_key}"
    }

    # Mapping of local files to Supabase sections
    mapping = {
        "kpis.json": "summary",
        "segment_kpis.json": "portfolio", # Simplified mapping
        "risk_alerts.json": "risk", # Assuming this exists or will be derived
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
            "decision_center_state.json": "decision", # Map to both for redundancy/compatibility
        }
        for filename, section in mapping_decision.items():
            file_path = decision_dir / filename
            if file_path.exists():
                _push_file(file_path, section, base_url, headers)

    for filename, section in mapping.items():
        file_path = run_dir / filename
        if file_path.exists():
            _push_file(file_path, section, base_url, headers)
        else:
            # Try subdirectories if any
            pass

def _push_file(file_path: Path, section: string, base_url: string, headers: Dict):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        url = f"{base_url}/{section}"
        print(f"Pushing {file_path.name} to {url}...")
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"Successfully synced {section}")
        else:
            print(f"Failed to sync {section}: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error syncing {file_path}: {e}")

if __name__ == "__main__":
    # Example usage: find latest run or pass as arg
    runs_dir = Path("logs/runs")
    if runs_dir.exists():
        runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
        if runs:
            latest_run = runs[0]
            print(f"Syncing latest run: {latest_run}")
            sync_to_supabase(latest_run)
        else:
            print("No runs found in logs/runs")
    else:
        print("logs/runs directory not found")
