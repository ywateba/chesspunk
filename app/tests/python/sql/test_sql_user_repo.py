"""
Tests for SQL User Repository
=============================
Tests all functions in core.repositories.sql.user_repo that interact with the SQL database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.sql.user_repo import SQLUserRepository
from core.schemas import schemas
from core.db import models


@pytest.mark.asyncio
async def test_get_user(db_session: AsyncSession):
    """Test getting a user by ID."""
    repo = SQLUserRepository(db_session)

    # Create a user first
    user_data = schemas.UserCreate(username="testuser", email="test@example.com", password="password")
    created_user = await repo.create_user(user_data, "hashed_password")

    # Get the user
    fetched_user = await repo.get_user(created_user.id)

    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.username == "testuser"
    assert fetched_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(db_session: AsyncSession):
    """Test getting a non-existent user."""
    repo = SQLUserRepository(db_session)

    fetched_user = await repo.get_user(99999)
    assert fetched_user is None


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession):
    """Test getting a user by email."""
    repo = SQLUserRepository(db_session)

    # Create a user
    user_data = schemas.UserCreate(username="testuser", email="test@example.com", password="password")
    created_user = await repo.create_user(user_data, "hashed_password")

    # Get by email
    fetched_user = await repo.get_user_by_email("test@example.com")

    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession):
    """Test getting a user by non-existent email."""
    repo = SQLUserRepository(db_session)

    fetched_user = await repo.get_user_by_email("nonexistent@example.com")
    assert fetched_user is None


@pytest.mark.asyncio
async def test_get_user_by_username(db_session: AsyncSession):
    """Test getting a user by username."""
    repo = SQLUserRepository(db_session)

    # Create a user
    user_data = schemas.UserCreate(username="testuser", email="test@example.com", password="password")
    created_user = await repo.create_user(user_data, "hashed_password")

    # Get by username
    fetched_user = await repo.get_user_by_username("testuser")

    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(db_session: AsyncSession):
    """Test getting a user by non-existent username."""
    repo = SQLUserRepository(db_session)

    fetched_user = await repo.get_user_by_username("nonexistentuser")
    assert fetched_user is None


@pytest.mark.asyncio
async def test_get_users(db_session: AsyncSession):
    """Test getting paginated list of users."""
    repo = SQLUserRepository(db_session)

    # Create multiple users
    users_data = [
        schemas.UserCreate(username="user1", email="user1@example.com", password="pass1"),
        schemas.UserCreate(username="user2", email="user2@example.com", password="pass2"),
        schemas.UserCreate(username="user3", email="user3@example.com", password="pass3"),
    ]

    for user_data in users_data:
        await repo.create_user(user_data, "hashed")

    # Get all users
    users = await repo.get_users()
    assert len(users) >= 3

    # Check that our users are in the list
    usernames = [user.username for user in users]
    assert "user1" in usernames
    assert "user2" in usernames
    assert "user3" in usernames


@pytest.mark.asyncio
async def test_get_users_pagination(db_session: AsyncSession):
    """Test users pagination."""
    repo = SQLUserRepository(db_session)

    # Create 5 users
    for i in range(5):
        user_data = schemas.UserCreate(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password="password"
        )
        await repo.create_user(user_data, "hashed")

    # Get first 2 users
    users = await repo.get_users(skip=0, limit=2)
    assert len(users) == 2

    # Get next 2 users
    users = await repo.get_users(skip=2, limit=2)
    assert len(users) == 2


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a new user."""
    repo = SQLUserRepository(db_session)

    user_data = schemas.UserCreate(username="newuser", email="new@example.com", password="password")
    created_user = await repo.create_user(user_data, "hashed_password")

    assert created_user.id is not None
    assert created_user.username == "newuser"
    assert created_user.email == "new@example.com"
    assert created_user.hashed_password == "hashed_password"
    assert created_user.elo == 1200  # default value


@pytest.mark.asyncio
async def test_update_user_elo(db_session: AsyncSession):
    """Test updating a user's Elo rating."""
    repo = SQLUserRepository(db_session)

    # Create a user
    user_data = schemas.UserCreate(username="testuser", email="test@example.com", password="password")
    created_user = await repo.create_user(user_data, "hashed")

    # Update Elo
    updated_user = await repo.update_user_elo(created_user.id, 1500)

    assert updated_user is not None
    assert updated_user.id == created_user.id
    assert updated_user.elo == 1500


@pytest.mark.asyncio
async def test_update_user_elo_not_found(db_session: AsyncSession):
    """Test updating Elo for non-existent user."""
    repo = SQLUserRepository(db_session)

    updated_user = await repo.update_user_elo(99999, 1500)
    assert updated_user is None