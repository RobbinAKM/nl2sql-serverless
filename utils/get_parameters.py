import boto3
import os

def get_ssm_parameter(name: str) -> str:
    """Fetches a SecureString parameter from AWS SSM."""
    ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]
