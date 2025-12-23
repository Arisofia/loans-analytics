#!/usr/bin/env python3
import argparse
import os
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ROOT = "https://api.github.com"


<<<<<<< HEAD
def build_request(url, token, data=None, method="GET"):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    encoded = json.dumps(data).encode("utf-8") if data is not None else None
    return urllib.request.Request(
        url,
        data=encoded,
        headers=headers,
        method=method,
    )
=======
def _create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session
>>>>>>> main

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
    parser.add_argument(
        "repo",
        help="Target repository in the format owner/name",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="Git ref to dispatch (default: main)",
    )
    parser.add_argument(
        "--workflows",
        nargs="+",
        help="Workflow names/IDs to dispatch; omit to dispatch all.",
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

    def workflow_label(workflow):
        name = workflow.get("name") or workflow.get("path") or ""
        workflow_id = workflow.get("id")
        identifier = workflow.get("file_name") or workflow.get("path")
        label_id = str(workflow_id) if workflow_id is not None else identifier
        return name, label_id

    id_lookup = {}
    name_lookup = {}
    available = []

    for workflow in workflows:
        name, label_id = workflow_label(workflow)
        if label_id:
            id_lookup[label_id] = workflow
        if name:
            name_lookup[name.lower()] = workflow
        display = name or label_id or "unknown"
        available.append(f"{display} (id={label_id})" if label_id else display)

    resolved = []
    for item in requested:
        match = id_lookup.get(item)
        if not match:
            match = name_lookup.get(item.lower())
        if not match:
            raise ValueError(
                "Workflow '{item}' not found; available: {choices}".format(
                    item=item, choices=", ".join(available)
                )
            )
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
<<<<<<< HEAD
        try:
            if trigger_workflow(args.repo, wf, args.ref, token):
                print(f"Dispatched {name} on {args.ref}")
                successes += 1
            else:
                print(f"Failed to dispatch {name} on {args.ref}")
        except urllib.error.HTTPError as error:
            message = error.read().decode("utf-8")
            sys.stderr.write(f"Dispatch failed for {name}: {message}\n")
=======
        if trigger_workflow(args.repo, wf, args.ref, token):
            print(f"Dispatched {name} on {args.ref}")
            successes += 1
        else:
            print(f"Failed to dispatch {name} on {args.ref}")
>>>>>>> main
        if args.delay:
            time.sleep(args.delay)
    if successes == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
