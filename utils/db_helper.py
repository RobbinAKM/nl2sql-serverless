import os
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_dynamodb_client():
    """Utility function to get the DynamoDB client, either for AWS or Local"""
    if os.getenv("USE_DYNAMODB_LOCAL").lower() == "true":
        logger.info("connecting to dynamoDB locally")
        return boto3.resource(
            "dynamodb",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            endpoint_url="http://localhost:8000"  # DynamoDB Local URL
        )
    else:
        logger.info("connecting to dynamoDB on AWS")
        return boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))

# Initialize DynamoDB client (will use local or AWS based on the environment)
dynamodb = get_dynamodb_client()

local_table= "SchemaTable"
aws_table = "SchemaTableV2"

def get_schema_by_id(schema_id):
    """Utility function to fetch schema from DynamoDB by schemaId"""
    table_name = os.getenv("DYNAMODB_TABLE", local_table)

    if not schema_id:
        raise ValueError("schemaId is required")

    try:
        # Access DynamoDB Table
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={"schemaId": schema_id})

        if "Item" not in response:
            raise ValueError(f"Schema with ID {schema_id} not found")

        return response["Item"]

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise FileNotFoundError(f"Table {table_name} not found")
        raise RuntimeError(f"DynamoDB ClientError: {str(e)}")

    except (BotoCoreError, Exception) as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")
