import os

import boto3


def upload_charts():
    bucket = os.environ.get("AWS_S3_BUCKET")
    if not bucket:
        print("Error: AWS_S3_BUCKET not set")
        return

    s3 = boto3.client("s3")
    source_dir = "exports/meta_agent"

    if not os.path.exists(source_dir):
        print(f"Error: Source directory {source_dir} not found")
        return

    for f in os.listdir(source_dir):
        if f.endswith(".png"):
            source_path = os.path.join(source_dir, f)
            target_key = f"dashboard_exports/{f}"
            s3.upload_file(
                source_path,
                bucket,
                target_key,
                ExtraArgs={"ACL": "public-read", "ContentType": "image/png"},
            )
            print(f"Uploaded {f} to s3://{bucket}/{target_key}")


if __name__ == "__main__":
    upload_charts()
