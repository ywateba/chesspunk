import pytest
import pytest_asyncio
import os
import aioboto3
from moto import mock_aws
from core.db.dynamodb import init_dynamodb, session
from core.config import settings

@pytest.fixture(scope="session", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["DB_ENGINE"] = "DYNAMODB"
    settings.DYNAMODB_ENDPOINT_URL = None

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_dynamodb(aws_credentials):
    """Start Moto DynamoDB mock and run Init Table functions globally per test."""
    with mock_aws():
        await init_dynamodb()
        yield 
