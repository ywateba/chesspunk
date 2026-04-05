import pytest
from core.schemas import schemas
from core.repositories.dynamodb.user_repo import DynamoUserRepository

@pytest.mark.asyncio
async def test_dynamo_user_repo_full_coverage():
    repo = DynamoUserRepository()
    user_schema = schemas.UserCreate(
        username="fulltest", email="full@test.com", password="pass", role="player", elo=1200
    )
    
    # 1. create_user
    created = await repo.create_user(user_schema, "hash")
    assert created.id is not None
    assert getattr(created, 'email') == "full@test.com"

    # 2. get_user
    fetched = await repo.get_user(str(created.id))
    assert fetched is not None
    assert str(fetched.id) == str(created.id)

    # 3. get_user_by_email
    by_email = await repo.get_user_by_email("full@test.com")
    assert by_email is not None
    assert str(by_email.id) == str(created.id)

    # 4. get_user_by_username
    by_username = await repo.get_user_by_username("fulltest")
    assert by_username is not None
    assert str(by_username.id) == str(created.id)

    # 5. get_users
    users = await repo.get_users(skip=0, limit=10)
    assert len(users) >= 1
    assert any(str(u.id) == str(created.id) for u in users)

    # 6. update_user_elo
    updated = await repo.update_user_elo(str(created.id), 2500)
    assert updated is not None
    assert getattr(updated, 'elo') == 2500

    # Negative hits
    assert await repo.get_user("invalid") is None
    assert await repo.get_user_by_email("invalid@test.com") is None
    assert await repo.get_user_by_username("invalid") is None
