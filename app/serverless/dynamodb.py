import boto3

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

def init_tables():
    dynamodb = boto3.client('dynamodb')
    existing_tables = dynamodb.list_tables().get("TableNames", [])
    
    for table_def in DYNAMODB_TABLES:
        if table_def["TableName"] not in existing_tables:
            dynamodb.create_table(**table_def)

def get_table(table_name: str):
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(table_name)
