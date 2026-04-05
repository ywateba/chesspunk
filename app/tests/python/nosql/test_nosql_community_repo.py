"""
Tests for MongoDB Community Repository
=====================================
Comprehensive test suite for MongoCommunityRepository covering all operations.
"""

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
import mongomock

# Patch mongomock.Database to ignore `authorizedCollections` missing keyword argument requested by Beanie>1.20 automatically
_original_list_collection_names = mongomock.Database.list_collection_names
def _patched_list_collection_names(self, *args, **kwargs):
    kwargs.pop('authorizedCollections', None)
    kwargs.pop('nameOnly', None)
    return _original_list_collection_names(self, *args, **kwargs)
mongomock.Database.list_collection_names = _patched_list_collection_names

from core.schemas import schemas
from core.db.documents import UserDocument, CommunityDocument
from core.repositories.nosql.user_repo import MongoUserRepository
from core.repositories.nosql.community_repo import MongoCommunityRepository


@pytest_asyncio.fixture(autouse=True)
async def init_mock_mongodb():
    """Initialize mock MongoDB for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("mongo_test_db"),
        document_models=[UserDocument, CommunityDocument]
    )
    yield


@pytest.mark.asyncio
class TestMongoCommunityRepository:
    """Test suite for MongoCommunityRepository."""

    @pytest.fixture
    async def community_repo(self):
        """Fixture providing a fresh community repository instance."""
        return MongoCommunityRepository()

    @pytest.fixture
    async def user_repo(self):
        """Fixture providing a fresh user repository instance."""
        return MongoUserRepository()

    @pytest.fixture
    async def sample_community_data(self):
        """Fixture providing sample community creation data."""
        return schemas.CommunityCreate(
            name="Test Chess Club",
            description="A community for chess enthusiasts",
            is_private=False
        )

    async def test_create_community(self, community_repo, user_repo, sample_community_data):
        """Test community creation with owner assignment."""
        # Create owner user
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        # Create community
        community = await community_repo.create_community(sample_community_data, owner.id)

        # Assertions
        assert community is not None
        assert community.id is not None
        assert community.name == sample_community_data.name
        assert community.description == sample_community_data.description
        assert community.is_private == sample_community_data.is_private
        assert community.owner_id == str(owner.id)
        assert len(community.members) == 1
        assert community.members[0].user_id == str(owner.id)
        assert community.members[0].role == "owner"
        assert community.created_at is not None

    async def test_get_community(self, community_repo, user_repo, sample_community_data):
        """Test retrieving community by ID."""
        # Create community
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        created_community = await community_repo.create_community(sample_community_data, owner.id)

        # Retrieve community
        retrieved_community = await community_repo.get_community(created_community.id)

        # Assertions
        assert retrieved_community is not None
        assert retrieved_community.id == created_community.id
        assert retrieved_community.name == sample_community_data.name
        assert retrieved_community.owner_id == str(owner.id)

    async def test_get_community_not_found(self, community_repo):
        """Test retrieving non-existent community returns None."""
        retrieved_community = await community_repo.get_community("nonexistent_id")
        assert retrieved_community is None

    async def test_get_communities_pagination(self, community_repo, user_repo):
        """Test retrieving communities with pagination."""
        # Create owner user
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        # Create multiple communities
        communities_data = [
            schemas.CommunityCreate(name=f"Community {i}", description=f"Description {i}")
            for i in range(5)
        ]

        created_communities = []
        for comm_data in communities_data:
            comm = await community_repo.create_community(comm_data, owner.id)
            created_communities.append(comm)

        # Test pagination
        all_communities = await community_repo.get_communities(skip=0, limit=10)
        assert len(all_communities) == 5

        # Test with limit
        limited_communities = await community_repo.get_communities(skip=0, limit=2)
        assert len(limited_communities) == 2

        # Test with skip
        skipped_communities = await community_repo.get_communities(skip=2, limit=10)
        assert len(skipped_communities) == 3

    async def test_get_communities_empty_database(self, community_repo):
        """Test retrieving communities from empty database."""
        communities = await community_repo.get_communities()
        assert communities == []

    async def test_join_community(self, community_repo, user_repo, sample_community_data):
        """Test user joining a community."""
        # Create community and users
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        member = await user_repo.create_user(
            schemas.UserCreate(username="member", email="member@test.com", password="pass"),
            "hash"
        )

        community = await community_repo.create_community(sample_community_data, owner.id)

        # Join community as member
        updated_community = await community_repo.join_community(community.id, member.id)

        # Assertions
        assert updated_community is not None
        assert len(updated_community.members) == 2
        assert any(m.user_id == str(owner.id) and m.role == "owner" for m in updated_community.members)
        assert any(m.user_id == str(member.id) and m.role == "member" for m in updated_community.members)

    async def test_join_community_custom_role(self, community_repo, user_repo, sample_community_data):
        """Test user joining a community with custom role."""
        # Create community and user
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        moderator = await user_repo.create_user(
            schemas.UserCreate(username="mod", email="mod@test.com", password="pass"),
            "hash"
        )

        community = await community_repo.create_community(sample_community_data, owner.id)

        # Join as moderator
        updated_community = await community_repo.join_community(community.id, moderator.id, "moderator")

        # Assertions
        assert len(updated_community.members) == 2
        assert any(m.user_id == str(moderator.id) and m.role == "moderator" for m in updated_community.members)

    async def test_join_community_twice(self, community_repo, user_repo, sample_community_data):
        """Test that joining a community twice doesn't create duplicate members."""
        # Create community and user
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        member = await user_repo.create_user(
            schemas.UserCreate(username="member", email="member@test.com", password="pass"),
            "hash"
        )

        community = await community_repo.create_community(sample_community_data, owner.id)

        # Join first time
        updated_community = await community_repo.join_community(community.id, member.id)
        assert len(updated_community.members) == 2

        # Join second time
        updated_community = await community_repo.join_community(community.id, member.id)
        assert len(updated_community.members) == 2  # Should still be 2

    async def test_join_nonexistent_community(self, community_repo, user_repo):
        """Test joining a non-existent community."""
        member = await user_repo.create_user(
            schemas.UserCreate(username="member", email="member@test.com", password="pass"),
            "hash"
        )

        # Try to join non-existent community
        result = await community_repo.join_community("nonexistent_id", member.id)
        assert result is None

    async def test_get_members(self, community_repo, user_repo, sample_community_data):
        """Test retrieving community members."""
        # Create community and multiple users
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        members = []
        for i in range(3):
            member = await user_repo.create_user(
                schemas.UserCreate(username=f"member{i}", email=f"member{i}@test.com", password="pass"),
                "hash"
            )
            members.append(member)

        community = await community_repo.create_community(sample_community_data, owner.id)

        # Add members
        for member in members:
            await community_repo.join_community(community.id, member.id)

        # Get members
        retrieved_members = await community_repo.get_members(community.id)

        # Assertions
        assert len(retrieved_members) == 4  # owner + 3 members
        member_ids = [m.user_id for m in retrieved_members]
        assert str(owner.id) in member_ids
        for member in members:
            assert str(member.id) in member_ids

    async def test_get_members_empty_community(self, community_repo, user_repo, sample_community_data):
        """Test getting members of community with only owner."""
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        community = await community_repo.create_community(sample_community_data, owner.id)

        # Get members (should only have owner)
        members = await community_repo.get_members(community.id)

        assert len(members) == 1
        assert members[0].user_id == str(owner.id)
        assert members[0].role == "owner"

    async def test_get_members_nonexistent_community(self, community_repo):
        """Test getting members of non-existent community."""
        members = await community_repo.get_members("nonexistent_id")
        assert members == []

    async def test_community_data_integrity(self, community_repo, user_repo):
        """Test that community data is stored and retrieved correctly."""
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        complex_community_data = schemas.CommunityCreate(
            name="Complex Community Name with Special Characters: !@#$%^&*()",
            description="A very detailed description that includes various special characters and long text to test data integrity. This description should be properly stored and retrieved without any corruption or truncation issues.",
            is_private=True
        )

        # Create community
        created_community = await community_repo.create_community(complex_community_data, owner.id)

        # Retrieve and verify
        retrieved_community = await community_repo.get_community(created_community.id)

        assert retrieved_community.name == complex_community_data.name
        assert retrieved_community.description == complex_community_data.description
        assert retrieved_community.is_private == complex_community_data.is_private
        assert retrieved_community.owner_id == str(owner.id)

    async def test_multiple_communities_isolation(self, community_repo, user_repo):
        """Test that multiple communities maintain data isolation."""
        # Create two communities with different owners
        owner1 = await user_repo.create_user(
            schemas.UserCreate(username="owner1", email="owner1@test.com", password="pass"),
            "hash1"
        )
        owner2 = await user_repo.create_user(
            schemas.UserCreate(username="owner2", email="owner2@test.com", password="pass"),
            "hash2"
        )

        comm1_data = schemas.CommunityCreate(name="Community 1", description="First community")
        comm2_data = schemas.CommunityCreate(name="Community 2", description="Second community")

        comm1 = await community_repo.create_community(comm1_data, owner1.id)
        comm2 = await community_repo.create_community(comm2_data, owner2.id)

        # Create a member user
        member = await user_repo.create_user(
            schemas.UserCreate(username="member", email="member@test.com", password="pass"),
            "hash"
        )

        # Add member to first community only
        await community_repo.join_community(comm1.id, member.id)

        # Verify isolation
        comm1_members = await community_repo.get_members(comm1.id)
        comm2_members = await community_repo.get_members(comm2.id)

        assert len(comm1_members) == 2  # owner1 + member
        assert len(comm2_members) == 1  # owner2 only

        assert str(member.id) in [m.user_id for m in comm1_members]
        assert str(member.id) not in [m.user_id for m in comm2_members]

    async def test_private_vs_public_communities(self, community_repo, user_repo):
        """Test private and public community creation."""
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        # Create private community
        private_data = schemas.CommunityCreate(
            name="Private Club",
            description="Private community",
            is_private=True
        )
        private_comm = await community_repo.create_community(private_data, owner.id)

        # Create public community
        public_data = schemas.CommunityCreate(
            name="Public Club",
            description="Public community",
            is_private=False
        )
        public_comm = await community_repo.create_community(public_data, owner.id)

        # Verify privacy settings
        assert private_comm.is_private == True
        assert public_comm.is_private == False

        # Both should be retrievable (privacy is handled at service layer)
        retrieved_private = await community_repo.get_community(private_comm.id)
        retrieved_public = await community_repo.get_community(public_comm.id)

        assert retrieved_private.is_private == True
        assert retrieved_public.is_private == False