"""
Tests for Auth API Endpoints
============================
Tests all endpoints in routers/auth.py that account for the database engine in use.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_signup_success(test_client: AsyncClient):
    """Test successful user signup."""
    response = await test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_signup_duplicate_fails(test_client: AsyncClient):
    """Test signup fails with duplicate username/email."""
    # Create first user
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    
    # Try to create duplicate
    response = await test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "newpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] in ["Email already registered", "Username already registered"]

@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient):
    """Test successful login."""
    # Create user first
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    
    # Login
    response = await test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_failure(test_client: AsyncClient):
    """Test login fails with wrong password."""
    # Create user first
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    
    # Try login with wrong password
    response = await test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401