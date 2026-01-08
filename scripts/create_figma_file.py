#!/usr/bin/env python3
"""Create a new Figma document via the Figma API."""

import argparse
import logging
import os
import sys
from typing import Optional

import requests

# Add src to path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def create_figma_file(name: str, project_id: Optional[str] = None, token: Optional[str] = None) -> Optional[str]:
    """Create a new Figma file.

    If project_id is None, it usually creates it in the user's Drafts.
    """
    api_token = token or os.getenv("FIGMA_TOKEN")
    if not api_token:
        logger.error("FIGMA_TOKEN not found in environment")
        return None

    url = "https://api.figma.com/v1/files"
    headers = {
        "X-Figma-Token": api_token,
        "Content-Type": "application/json",
    }

    payload = {
        "name": name,
    }
    if project_id:
        payload["project_id"] = project_id

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        file_key = data.get("key")
        if file_key:
            logger.info(f"Successfully created Figma file: {name}")
            logger.info(f"File Key: {file_key}")
            logger.info(f"URL: https://www.figma.com/file/{file_key}")
            return file_key

        logger.error(f"Figma API did not return a file key: {data}")
        return None

    except requests.RequestException as e:
        logger.error(f"Failed to create Figma file: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Create a new Figma document")
    parser.add_argument("--name", default="Abaco Loans Analytics Dashboard", help="Name of the new Figma file")
    parser.add_argument("--project-id", help="Optional Figma Project ID (defaults to Drafts if omitted)")
    parser.add_argument("--token", help="Figma API Token (overrides FIGMA_TOKEN env var)")

    args = parser.parse_args()

    file_key = create_figma_file(args.name, args.project_id, args.token)

    if file_key:
        print(f"SUCCESS: {file_key}")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
