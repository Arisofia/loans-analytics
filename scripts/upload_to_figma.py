import os

FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")  # Set this in your environment or .env file
FIGMA_FILE_KEY = os.getenv("FIGMA_FILE_KEY")  # Set this to your Figma file key
FIGMA_NODE_ID = os.getenv("FIGMA_NODE_ID")  # Set this to the node (frame) ID to update

UPLOAD_IMAGE_PATH = "exports/figma/growth_chart.png"


def upload_image_to_figma(image_path, file_key, node_id, token):
    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    headers = {
        "X-Figma-Token": token,
    }

    # Figma does not support direct image upload via API; workaround is to use the Images endpoint to link an image URL.
    # For demo, this will just print instructions. For production, upload to a public URL (S3, etc.) and patch the node.
    print("Figma API does not support direct image upload. Upload your image to a public URL, then use the Figma Images API to update the node.")
    print(f"Image path: {image_path}")
    print(f"Figma file key: {file_key}")
    print(f"Figma node id: {node_id}")
    print(f"Token: {token[:6]}... (truncated)")
    # Example PATCH request (after uploading image to a public URL):
    # requests.patch(
    #     f"https://api.figma.com/v1/files/{file_key}/images",
    #     headers=headers,
    #     json={"ids": node_id, "image_url": "https://your-public-url.com/growth_chart.png"}
    # )

if __name__ == "__main__":
    if not (FIGMA_TOKEN and FIGMA_FILE_KEY and FIGMA_NODE_ID):
        print("Please set FIGMA_TOKEN, FIGMA_FILE_KEY, and FIGMA_NODE_ID as environment variables.")
        exit(1)
    upload_image_to_figma(UPLOAD_IMAGE_PATH, FIGMA_FILE_KEY, FIGMA_NODE_ID, FIGMA_TOKEN)
