import os
from core.db.dynamodb import session
from core.config import settings

def get_resource():
    return session.resource(
        'dynamodb',
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        region_name=settings.DYNAMODB_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "dummy"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")
    )

class DynamoItem:
    """A mock object to safely wrap DynamoDB dicts imitating ODMs."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
