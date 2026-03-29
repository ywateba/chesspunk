import sys
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.db.database import get_db
from core.db.models import Base
from routers.main import app





# --- Tests ---

def test_signup_success(test_client: TestClient, db_session: Session ):
    response = test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_signup_duplicate_fails(test_client: TestClient, db_session: Session ):
    test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    # Attempting to sign up with the same username/email should fail
    response = test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "newpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] in ["Email already registered", "Username already registered"]

def test_login_success(test_client: TestClient, db_session: Session ):
    test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    response = test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(test_client: TestClient, db_session: Session ):
    test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    response = test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_create_competition_unauthorized(test_client: TestClient, db_session: Session ):
    response = test_client.post(
        "/competitions/",
        json={"name": "Winter Tournament"}
    )
    assert response.status_code == 401 # Unauthorized because no token is provided

def test_create_and_join_competition_authorized(test_client: TestClient, db_session: Session ):
    test_client.post("/auth/signup", json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"})
    
    # 1. Login to get token
    login_res = test_client.post("/auth/login", data={"username": "testuser", "password": "secretpassword"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create competition
    comp_res = test_client.post("/competitions/", json={"name": "Winter Tournament"}, headers=headers)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]
    
    # 3. Join competition
    join_res = test_client.post(f"/competitions/{comp_id}/join", headers=headers)
    assert join_res.status_code == 200
    assert len(join_res.json()["players"]) == 1
    assert join_res.json()["players"][0]["username"] == "testuser"

def test_signup_duplicate_username_fails(test_client: TestClient, db_session: Session):
    test_client.post("/auth/signup", json={"username": "conflictuser", "email": "good@example.com", "password": "pass"})
    response = test_client.post("/auth/signup", json={"username": "conflictuser", "email": "different@example.com", "password": "pass"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_invalid_token(test_client: TestClient, db_session: Session):
    headers = {"Authorization": "Bearer BAD_TOKEN"}
    res = test_client.get("/users/me", headers=headers)
    assert res.status_code == 401

from core.auth.utils import create_access_token
def test_create_access_token_default_expire():
    token = create_access_token(data={"sub": "testuser"})
    assert token is not None