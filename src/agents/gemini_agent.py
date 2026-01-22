import os
import boto3
from google import genai
from google.genai import types


class GeminiAgent:
    def __init__(self, aws_access_key=None, aws_secret_key=None, region_name=None):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region_name or os.getenv("AWS_REGION", "us-east-1"),
        )
        self.client = genai.Client()

    def get_signed_url(self, bucket, key, expires=3600):
        return self.s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
        )

    def analyze_documents(
        self, public_url, s3_bucket, s3_key, prompt="What are these documents about?"
    ):
        signed_url = self.get_signed_url(s3_bucket, s3_key)
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Part.from_uri(file_uri=public_url),
                types.Part.from_uri(file_uri=signed_url),
                prompt,
            ],
        )
        return response.text
