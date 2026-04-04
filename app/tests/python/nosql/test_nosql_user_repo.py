"""
Tests for MongoDB User Repository
=================================
Comprehensive test suite for MongoUserRepository covering all CRUD operations.
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
from core.db.documents import UserDocument
from core.repositories.nosql.user_repo import MongoUserRepository


@pytest_asyncio.fixture(autouse=True)
async def init_mock_mongodb():
    """Initialize mock MongoDB for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[UserDocument]
    )
    yield


@pytest.mark.asyncio
class TestMongoUserRepository:
    """Test suite for MongoUserRepository."""

    @pytest.fixture
    async def user_repo(self):
        """Fixture providing a fresh user repository instance."""
        return MongoUserRepository()

    @pytest.fixture
    async def sample_user_data(self):
        """Fixture providing sample user creation data."""
        return schemas.UserCreate(
            username="testuser",
            email="test@example.com",
            password="securepassword123"
        )

    async def test_create_user(self, user_repo, sample_user_data):
        """Test user creation with proper data persistence."""
        hashed_password = "hashed_password_123"

        # Create user
        user = await user_repo.create_user(sample_user_data, hashed_password)

        # Assertions
        assert user is not None
        assert user.id is not None
        assert user.username == sample_user_data.username
        assert user.email == sample_user_data.email
        assert user.hashed_password == hashed_password
        assert user.elo == 1200  # Default Elo rating
        assert user.created_at is not None

    async def test_get_user(self, user_repo, sample_user_data):
        """Test retrieving user by ID."""
        hashed_password = "hashed_password_123"

        # Create user
        created_user = await user_repo.create_user(sample_user_data, hashed_password)

        # Retrieve user by ID (convert to int for repository interface)
        retrieved_user = await user_repo.get_user(int(str(created_user.id)))

        # Assertions
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == sample_user_data.username
        assert retrieved_user.email == sample_user_data.email

    async def test_get_user_not_found(self, user_repo):
        """Test retrieving non-existent user returns None."""
        retrieved_user = await user_repo.get_user(99999)
        assert retrieved_user is None

    async def test_get_user_by_email(self, user_repo, sample_user_data):
        """Test retrieving user by email address."""
        hashed_password = "hashed_password_123"

        # Create user
        created_user = await user_repo.create_user(sample_user_data, hashed_password)

        # Retrieve user by email
        retrieved_user = await user_repo.get_user_by_email(sample_user_data.email)

        # Assertions
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == sample_user_data.email

    async def test_get_user_by_email_not_found(self, user_repo):
        """Test retrieving user by non-existent email returns None."""
        retrieved_user = await user_repo.get_user_by_email("nonexistent@example.com")
        assert retrieved_user is None

    async def test_get_user_by_username(self, user_repo, sample_user_data):
        """Test retrieving user by username."""
        hashed_password = "hashed_password_123"

        # Create user
        created_user = await user_repo.create_user(sample_user_data, hashed_password)

        # Retrieve user by username
        retrieved_user = await user_repo.get_user_by_username(sample_user_data.username)

        # Assertions
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == sample_user_data.username

    async def test_get_user_by_username_not_found(self, user_repo):
        """Test retrieving user by non-existent username returns None."""
        retrieved_user = await user_repo.get_user_by_username("nonexistentuser")
        assert retrieved_user is None

    async def test_get_users_pagination(self, user_repo):
        """Test retrieving users with pagination."""
        hashed_password = "hashed_password_123"

        # Create multiple users
        users_data = [
            schemas.UserCreate(username=f"user{i}", email=f"user{i}@example.com", password="pass")
            for i in range(5)
        ]

        created_users = []
        for user_data in users_data:
            user = await user_repo.create_user(user_data, hashed_password)
            created_users.append(user)

        # Test pagination
        all_users = await user_repo.get_users(skip=0, limit=10)
        assert len(all_users) == 5

        # Test with limit
        limited_users = await user_repo.get_users(skip=0, limit=2)
        assert len(limited_users) == 2

        # Test with skip
        skipped_users = await user_repo.get_users(skip=2, limit=10)
        assert len(skipped_users) == 3

    async def test_get_users_empty_database(self, user_repo):
        """Test retrieving users from empty database."""
        users = await user_repo.get_users()
        assert users == []

    async def test_update_user_elo(self, user_repo, sample_user_data):
        """Test updating user Elo rating."""
        hashed_password = "hashed_password_123"
        new_elo = 1500

        # Create user
        created_user = await user_repo.create_user(sample_user_data, hashed_password)
        assert created_user.elo == 1200  # Default Elo

        # Update Elo
        updated_user = await user_repo.update_user_elo(int(str(created_user.id)), new_elo)

        # Assertions
        assert updated_user is not None
        assert updated_user.id == created_user.id
        assert updated_user.elo == new_elo

    async def test_update_user_elo_not_found(self, user_repo):
        """Test updating Elo for non-existent user returns None."""
        updated_user = await user_repo.update_user_elo(99999, 1500)
        assert updated_user is None

    async def test_duplicate_email_creation(self, user_repo):
        """Test that duplicate emails are allowed (handled at service layer)."""
        hashed_password = "hashed_password_123"

        user1_data = schemas.UserCreate(username="user1", email="same@example.com", password="pass")
        user2_data = schemas.UserCreate(username="user2", email="same@example.com", password="pass")

        # Both should succeed at repository level
        user1 = await user_repo.create_user(user1_data, hashed_password)
        user2 = await user_repo.create_user(user2_data, hashed_password)

        assert user1 is not None
        assert user2 is not None
        assert user1.id != user2.id
        assert user1.email == user2.email

    async def test_duplicate_username_creation(self, user_repo):
        """Test that duplicate usernames are allowed (handled at service layer)."""
        hashed_password = "hashed_password_123"

        user1_data = schemas.UserCreate(username="sameuser", email="user1@example.com", password="pass")
        user2_data = schemas.UserCreate(username="sameuser", email="user2@example.com", password="pass")

        # Both should succeed at repository level
        user1 = await user_repo.create_user(user1_data, hashed_password)
        user2 = await user_repo.create_user(user2_data, hashed_password)

        assert user1 is not None
        assert user2 is not None
        assert user1.id != user2.id
        assert user1.username == user2.username

    async def test_user_data_integrity(self, user_repo):
        """Test that user data is stored and retrieved correctly."""
        hashed_password = "complex_hashed_password_with_special_chars_!@#$%^&*()"
        user_data = schemas.UserCreate(
            username="complex_user",
            email="complex.email+tag@example.com",
            password="verylongpasswordthatshouldbehandledcorrectly"
        )

        # Create user
        created_user = await user_repo.create_user(user_data, hashed_password)

        # Retrieve and verify
        retrieved_user = await user_repo.get_user(int(str(created_user.id)))

        assert retrieved_user.username == user_data.username
        assert retrieved_user.email == user_data.email
        assert retrieved_user.hashed_password == hashed_password
        assert retrieved_user.elo == 1200