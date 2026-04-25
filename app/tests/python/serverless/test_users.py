import os
from unittest.mock import patch
from serverless.dynamodb import initialize_tables
from serverless.handlers import users

@patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1"})
def test_user_lifecycle(aws_credentials, dynamodb_mock):
    # Ensure tables are created in the mock DB natively
    initialize_tables()

    # 1. Create a user via explicit core function
    user = users.create_user({"email": "test@chesspunk.com", "role": "player", "elo": 1500})
    user_id = user["id"]
    
    # 2. Get User
    retrieved = users.get_user(user_id)
    assert retrieved["email"] == "test@chesspunk.com"
    
    # 3. Update User
    users.update_user(user_id, {"elo": 1600})
    retrieved = users.get_user(user_id)
    assert retrieved["elo"] == 1600
    
    # 4. List Users
    all_users = users.list_users()
    assert len(all_users) == 1
    
    # 5. Delete User
    users.delete_user(user_id)
    assert not users.get_user(user_id)
