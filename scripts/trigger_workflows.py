#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://api.github.com"


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


def ensure_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.stderr.write("GITHUB_TOKEN is required\n")
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
    request = build_request(url, token)
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload.get("workflows", [])


def resolve_workflow_targets(workflows, requested):
    if not requested:
        return workflows

    id_lookup = {}
    name_lookup = {}
    available = []

    for workflow in workflows:
        workflow_id = workflow.get("id")
        name = workflow.get("name", "")

        if workflow_id is not None:
            id_lookup[str(workflow_id)] = workflow
        name_lookup[name.lower()] = workflow
        available.append(f"{name} (id={workflow_id})")

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
    request = build_request(url, token, {"ref": ref}, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.status == 204


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
        try:
            if trigger_workflow(args.repo, wf, args.ref, token):
                print(f"Dispatched {name} on {args.ref}")
                successes += 1
            else:
                print(f"Failed to dispatch {name} on {args.ref}")
        except urllib.error.HTTPError as error:
            message = error.read().decode("utf-8")
            sys.stderr.write(f"Dispatch failed for {name}: {message}\n")
        if args.delay:
            time.sleep(args.delay)
    if successes == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
