import pytest
import os
from moto import mock_aws
import sys

# Ensure the 'app' root resolves gracefully under pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from serverless.dynamodb import init_tables

@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials forcing native moto intercepts."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    
    with mock_aws():
        init_tables()
        yield 
