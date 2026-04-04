"""
Tests for SQL Community Repository
==================================
Tests all functions in core.repositories.sql.community_repo that interact with the SQL database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.sql.community_repo import SQLCommunityRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.schemas import schemas
from core.db import models


@pytest.mark.asyncio
async def test_create_community(db_session: AsyncSession):
    """Test creating a new community."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create an owner user
    user_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(user_data, "hashed")

    # Create community
    comm_data = schemas.CommunityCreate(name="Test Community", description="A test community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    assert created_comm.id is not None
    assert created_comm.name == "Test Community"
    assert created_comm.description == "A test community"
    assert created_comm.owner_id == owner.id

    # Check that owner was automatically added as a member
    members = await community_repo.get_members(created_comm.id)
    assert len(members) == 1
    assert members[0].user_id == owner.id
    assert members[0].role == "owner"


@pytest.mark.asyncio
async def test_get_community(db_session: AsyncSession):
    """Test getting a community by ID."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create a community
    user_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(user_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    # Get the community
    fetched_comm = await community_repo.get_community(created_comm.id)

    assert fetched_comm is not None
    assert fetched_comm.id == created_comm.id
    assert fetched_comm.name == "Test Community"


@pytest.mark.asyncio
async def test_get_community_not_found(db_session: AsyncSession):
    """Test getting a non-existent community."""
    repo = SQLCommunityRepository(db_session)

    fetched_comm = await repo.get_community(99999)
    assert fetched_comm is None


@pytest.mark.asyncio
async def test_get_community_with_string_id(db_session: AsyncSession):
    """Test getting a community with string ID (should convert to int)."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create a community
    user_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(user_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    # Get the community using string ID
    fetched_comm = await community_repo.get_community(str(created_comm.id))

    assert fetched_comm is not None
    assert fetched_comm.id == created_comm.id


@pytest.mark.asyncio
async def test_get_communities(db_session: AsyncSession):
    """Test getting paginated list of communities."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create an owner user
    user_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(user_data, "hashed")

    # Create multiple communities
    comms_data = [
        schemas.CommunityCreate(name="Community 1"),
        schemas.CommunityCreate(name="Community 2"),
        schemas.CommunityCreate(name="Community 3"),
    ]

    for comm_data in comms_data:
        await community_repo.create_community(comm_data, owner.id)

    # Get all communities
    communities = await community_repo.get_communities()
    assert len(communities) >= 3

    # Check that our communities are in the list
    names = [comm.name for comm in communities]
    assert "Community 1" in names
    assert "Community 2" in names
    assert "Community 3" in names


@pytest.mark.asyncio
async def test_get_communities_pagination(db_session: AsyncSession):
    """Test communities pagination."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create an owner user
    user_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(user_data, "hashed")

    # Create 5 communities
    for i in range(5):
        comm_data = schemas.CommunityCreate(name=f"Community {i}")
        await community_repo.create_community(comm_data, owner.id)

    # Get first 2 communities
    communities = await community_repo.get_communities(skip=0, limit=2)
    assert len(communities) == 2

    # Get next 2 communities
    communities = await community_repo.get_communities(skip=2, limit=2)
    assert len(communities) == 2


@pytest.mark.asyncio
async def test_join_community(db_session: AsyncSession):
    """Test joining a community as a member."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and user
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    # Create another user to join
    member_data = schemas.UserCreate(username="member", email="member@example.com", password="password")
    member = await user_repo.create_user(member_data, "hashed")

    # Join community
    membership = await community_repo.join_community(created_comm.id, member.id, "member")

    assert membership.community_id == created_comm.id
    assert membership.user_id == member.id
    assert membership.role == "member"

    # Check members
    members = await community_repo.get_members(created_comm.id)
    assert len(members) == 2  # owner + new member

    member_ids = [m.user_id for m in members]
    assert owner.id in member_ids
    assert member.id in member_ids


@pytest.mark.asyncio
async def test_join_community_as_moderator(db_session: AsyncSession):
    """Test joining a community with moderator role."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and user
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    # Create moderator user
    mod_data = schemas.UserCreate(username="moderator", email="mod@example.com", password="password")
    moderator = await user_repo.create_user(mod_data, "hashed")

    # Join as moderator
    membership = await community_repo.join_community(created_comm.id, moderator.id, "moderator")

    assert membership.role == "moderator"


@pytest.mark.asyncio
async def test_get_members(db_session: AsyncSession):
    """Test getting all members of a community."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    # Add multiple members
    for i in range(3):
        user_data = schemas.UserCreate(
            username=f"member{i}",
            email=f"member{i}@example.com",
            password="password"
        )
        user = await user_repo.create_user(user_data, "hashed")
        await community_repo.join_community(created_comm.id, user.id, "member")

    # Get members
    members = await community_repo.get_members(created_comm.id)

    assert len(members) == 4  # owner + 3 members
    roles = [m.role for m in members]
    assert "owner" in roles
    assert roles.count("member") == 3


@pytest.mark.asyncio
async def test_get_members_empty_community(db_session: AsyncSession):
    """Test getting members of a community with no additional members."""
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community (owner is automatically added)
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    created_comm = await community_repo.create_community(comm_data, owner.id)

    # Get members (should only have owner)
    members = await community_repo.get_members(created_comm.id)

    assert len(members) == 1
    assert members[0].user_id == owner.id
    assert members[0].role == "owner"