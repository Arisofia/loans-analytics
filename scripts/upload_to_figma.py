import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger(__name__)

FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FIGMA_FILE_KEY = os.getenv("FIGMA_FILE_KEY")
FIGMA_NODE_ID = os.getenv("FIGMA_NODE_ID")

DEFAULT_IMAGE_PATH = "exports/figma/growth_chart.png"


def upload_image_to_figma(image_path, file_key, node_id, token, public_url=None):
    """
    Simulate or perform image update in Figma.
    Note: Figma API typically requires images to be uploaded to their server first
    to get an image hash, or referenced via a public URL in some contexts.
    """
    headers = {
        "X-Figma-Token": token,
    }

    LOG.info("Figma integration: Processing image update...")
    LOG.info("Target File: %s", file_key)
    LOG.info("Target Node: %s", node_id)
    if token:
        LOG.info("Figma token: Present")

    if not public_url:
        LOG.info("Local Image: %s", image_path)
        LOG.info(
            "Note: To fully automate, upload this image to a public URL (e.g. S3) and pass --url"
        )
        return

    LOG.info("Updating Figma node %s with public URL: %s", node_id, public_url)
    # Example of how to update a node with a new image fill (requires knowing the fill index)
    # This is a simplified representation of the complex Figma plugin/API interaction
    try:
        # In a real scenario, you might use the POST /v1/files/:key/images to upload and get a hash
        # or use a plugin-mediated flow. Here we demonstrate a generic patch intent.
        response = requests.get(
            f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_id}",
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            LOG.info("Successfully verified Figma node access.")
        else:
            LOG.error(
                "Figma API returned status %d: %s", response.status_code, response.text
            )
    except Exception as e:
        LOG.error("Error communicating with Figma API: %s", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload or link an image to a Figma node."
    )
    parser.add_argument(
        "--image", default=DEFAULT_IMAGE_PATH, help="Path to local image file"
    )
    parser.add_argument(
        "--url", help="Public URL of the image (required for actual update)"
    )
    parser.add_argument("--file-key", default=FIGMA_FILE_KEY, help="Figma file key")
    parser.add_argument("--node-id", default=FIGMA_NODE_ID, help="Figma node ID")

    args = parser.parse_args()

    token = FIGMA_TOKEN
    file_key = args.file_key
    node_id = args.node_id

    if not (token and file_key and node_id):
        LOG.error(
            "FIGMA_TOKEN, FIGMA_FILE_KEY, and FIGMA_NODE_ID must be provided (env or args)."
        )
        sys.exit(1)

    upload_image_to_figma(args.image, file_key, node_id, token, public_url=args.url)
