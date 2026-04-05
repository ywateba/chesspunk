"""
Tests for Users API Endpoints
=============================
Tests all endpoints in routers/users.py that account for the database engine in use.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from core.auth.utils import create_access_token


@pytest.mark.asyncio
async def test_get_current_user_profile(test_client: AsyncClient):
    """Test getting the current user's profile."""
    # First create a user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"}
    )
    assert signup_response.status_code == 200
    user_data = signup_response.json()

    # Login to get token
    login_response = await test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secretpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Get current user profile
    response = await test_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    profile_data = response.json()

    assert profile_data["id"] == user_data["id"]
    assert profile_data["username"] == "testuser"
    assert profile_data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_profile_unauthorized(test_client: AsyncClient):
    """Test getting current user profile without authentication."""
    response = await test_client.get("/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_users_list(test_client: AsyncClient):
    """Test getting paginated list of users."""
    # Create multiple users
    users_data = [
        {"username": "user1", "email": "user1@example.com", "password": "password1"},
        {"username": "user2", "email": "user2@example.com", "password": "password2"},
        {"username": "user3", "email": "user3@example.com", "password": "password3"},
    ]

    for user in users_data:
        response = await test_client.post("/auth/signup", json=user)
        assert response.status_code == 200

    # Get users list
    response = await test_client.get("/users/")
    assert response.status_code == 200
    users_list = response.json()

    assert len(users_list) == 3
    usernames = [user["username"] for user in users_list]
    assert "user1" in usernames
    assert "user2" in usernames
    assert "user3" in usernames


@pytest.mark.asyncio
async def test_get_users_list_pagination(test_client: AsyncClient):
    """Test users list pagination."""
    # Create 5 users
    for i in range(5):
        user_data = {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "password": "password"
        }
        response = await test_client.post("/auth/signup", json=user_data)
        assert response.status_code == 200

    # Get first 2 users
    response = await test_client.get("/users/?skip=0&limit=2")
    assert response.status_code == 200
    users_list = response.json()
    assert len(users_list) == 2

    # Get next 2 users
    response = await test_client.get("/users/?skip=2&limit=2")
    assert response.status_code == 200
    users_list = response.json()
    assert len(users_list) == 2

    # Get remaining user
    response = await test_client.get("/users/?skip=4&limit=2")
    assert response.status_code == 200
    users_list = response.json()
    assert len(users_list) == 1


@pytest.mark.asyncio
async def test_get_users_list_empty(test_client: AsyncClient):
    """Test getting users list when no users exist."""
    response = await test_client.get("/users/")
    assert response.status_code == 200
    users_list = response.json()
    assert users_list == []


@pytest.mark.asyncio
async def test_get_users_list_large_limit(test_client: AsyncClient):
    """Test users list with large limit."""
    # Create 3 users
    for i in range(3):
        user_data = {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "password": "password"
        }
        response = await test_client.post("/auth/signup", json=user_data)
        assert response.status_code == 200

    # Get all users with large limit
    response = await test_client.get("/users/?limit=1000")
    assert response.status_code == 200
    users_list = response.json()
    assert len(users_list) == 3