import sys
import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from core.auth.utils import create_access_token

async def test_signup_success(test_client: AsyncClient, db_session: AsyncSession):
    response = await test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

async def test_signup_duplicate_fails(test_client: AsyncClient, db_session: AsyncSession):
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    response = await test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "newpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] in ["Email already registered", "Username already registered"]

async def test_login_success(test_client: AsyncClient, db_session: AsyncSession):
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    response = await test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_login_failure(test_client: AsyncClient, db_session: AsyncSession):
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    response = await test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401

async def test_create_competition_unauthorized(test_client: AsyncClient, db_session: AsyncSession):
    response = await test_client.post(
        "/competitions/",
        json={"name": "Winter Tournament"}
    )
    assert response.status_code == 401 

async def test_create_and_join_competition_authorized(test_client: AsyncClient, db_session: AsyncSession):
    await test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    
    from core.db import models
    from sqlalchemy.future import select
    res = await db_session.execute(select(models.User).where(models.User.username == "testuser"))
    u = res.scalars().first()
    u.role = "admin"
    await db_session.commit()
    
    login_res = await test_client.post("/auth/login", data={"username": "testuser", "password": "secretpassword"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    comp_res = await test_client.post("/competitions/", json={"name": "Winter Tournament"}, headers=headers)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]
    
    join_res = await test_client.post(f"/competitions/{comp_id}/join", headers=headers)
    assert join_res.status_code == 200
    assert len(join_res.json()["players"]) == 1
    assert join_res.json()["players"][0]["username"] == "testuser"

async def test_signup_duplicate_username_fails(test_client: AsyncClient, db_session: AsyncSession):
    await test_client.post("/auth/signup", json={"username": "conflictuser", "email": "good@example.com", "password": "pass"})
    response = await test_client.post("/auth/signup", json={"username": "conflictuser", "email": "different@example.com", "password": "pass"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

async def test_invalid_token(test_client: AsyncClient, db_session: AsyncSession):
    headers = {"Authorization": "Bearer BAD_TOKEN"}
    res = await test_client.get("/users/me", headers=headers)
    assert res.status_code == 401

async def test_create_access_token_default_expire():
    token = create_access_token(data={"sub": "testuser"})
    assert token is not None