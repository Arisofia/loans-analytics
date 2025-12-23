#!/usr/bin/env python3
import argparse
import os
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ROOT = "https://api.github.com"


def _create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


SESSION = _create_session()


def ensure_token():
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        sys.stderr.write("GITHUB_TOKEN or GH_TOKEN is required\n")
        sys.exit(1)
    return token


def parse_args():
    parser = argparse.ArgumentParser(
        description="Trigger GitHub Actions workflows via workflow_dispatch"
    )
    parser.add_argument("repo", help="Target repository in the format owner/name")
    parser.add_argument(
        "--ref", default="main", help="Git ref to dispatch (default: main)"
    )
    parser.add_argument(
        "--workflows",
        nargs="+",
        help=(
            "Workflow names or IDs to dispatch. "
            "If omitted, all workflows will be dispatched."
        ),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait between dispatch calls",
    )
    return parser.parse_args()


def fetch_workflows(repo, token):
    url = f"{API_ROOT}/repos/{repo}/actions/workflows"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = SESSION.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("workflows", [])
    except requests.exceptions.RequestException as error:
        sys.stderr.write(f"Error fetching workflows: {error}\n")
        if error.response is not None:
            sys.stderr.write(f"Response: {error.response.text}\n")
        sys.exit(1)


def resolve_workflow_targets(workflows, requested):
    if not requested:
        return workflows
    resolved = []
    for item in requested:
        if item.isdigit():
            match = next(
                (wf for wf in workflows if str(wf.get("id")) == item), None
            )
        else:
            match = next(
                (wf for wf in workflows
                 if wf.get("name", "").lower() == item.lower()),
                None
            )
        if not match:
            raise ValueError(f"Workflow '{item}' not found")
        resolved.append(match)
    return resolved


def trigger_workflow(repo, workflow, ref, token):
    identifier = workflow.get("id") or workflow.get("file_name")
    url = f"{API_ROOT}/repos/{repo}/actions/workflows/{identifier}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"ref": ref}
    try:
        response = SESSION.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as error:
        name = workflow.get("name", "unknown")
        sys.stderr.write(f"Error dispatching workflow '{name}': {error}\n")
        if error.response is not None:
            sys.stderr.write(f"Response: {error.response.text}\n")
        return False


def main():
    args = parse_args()
    token = ensure_token()
    workflows = fetch_workflows(args.repo, token)
    targets = resolve_workflow_targets(workflows, args.workflows)
    if not targets:
        sys.stderr.write("No workflows available to dispatch\n")
        sys.exit(1)
    successes = 0
    for wf in targets:
        name = wf.get("name") or wf.get("path")
        if trigger_workflow(args.repo, wf, args.ref, token):
            print(f"Dispatched {name} on {args.ref}")
            successes += 1
        else:
            print(f"Failed to dispatch {name} on {args.ref}")
        if args.delay:
            time.sleep(args.delay)
    if successes == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
