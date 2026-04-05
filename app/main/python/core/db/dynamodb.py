import aioboto3
import os
from typing import List, Dict, Any
from core.config import settings

session = aioboto3.Session()

DYNAMODB_TABLES = [
    {
        "TableName": "Users",
        "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": "Competitions",
        "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": "Matches",
        "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": "Communities",
        "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": "Social",
        "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST"
    }
]

async def init_dynamodb() -> None:
    """Initializes tables asynchronously on startup if they don't exist."""
    async with session.client(
        'dynamodb', 
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL, 
        region_name=settings.DYNAMODB_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "dummy"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")
    ) as client:
        existing_tables_resp = await client.list_tables()
        existing_tables = existing_tables_resp.get("TableNames", [])
        
        for table in DYNAMODB_TABLES:
            if table["TableName"] not in existing_tables:
                await client.create_table(**table)
