import pytest
from core.schemas import schemas
from core.repositories.dynamodb.community_repo import DynamoCommunityRepository

@pytest.mark.asyncio
async def test_dynamo_community_repo_full_coverage():
    repo = DynamoCommunityRepository()
    
    # 1. create_community
    schema = schemas.CommunityCreate(name="Open Chess", description="Open to all")
    owner_id = "owner-999"
    comm = await repo.create_community(schema, owner_id)
    assert comm is not None
    assert getattr(comm, 'owner_id') == owner_id
    assert len(getattr(comm, 'members')) == 1

    # 2. get_community
    fetched = await repo.get_community(str(comm.id))
    assert fetched is not None
    assert str(fetched.id) == str(comm.id)

    # 3. join_community
    joined = await repo.join_community(str(comm.id), "player-888", "player")
    assert len(getattr(joined, 'members')) == 2

    # Duplicate join
    joined = await repo.join_community(str(comm.id), "player-888", "player")
    assert len(getattr(joined, 'members')) == 2

    # 4. get_members
    members = await repo.get_members(str(comm.id))
    assert len(members) == 2
    assert any(m.get('user_id') == 'player-888' for m in members)

    # 5. get_communities
    comms = await repo.get_communities()
    assert len(comms) >= 1
    assert any(str(c.id) == str(comm.id) for c in comms)

    # Failures
    assert await repo.get_community("invalid") is None
    assert await repo.join_community("invalid", "123") is None
    assert await repo.get_members("invalid") == []
