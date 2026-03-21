import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the 'main' directory to the path so we can import the modules easily
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../main')))

from main import app
from database import Base, get_db

# --- Setup In-Memory Test Database ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the test database
Base.metadata.create_all(bind=engine)

# Override the dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Tests ---

def test_signup_success():
    response = client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_signup_duplicate_fails():
    # Attempting to sign up with the same username/email should fail
    response = client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "newpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email or username already registered"

def test_login_success():
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secretpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure():
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_create_competition_unauthorized():
    response = client.post(
        "/competitions/",
        json={"name": "Winter Tournament"}
    )
    assert response.status_code == 401 # Unauthorized because no token is provided

def test_create_and_join_competition_authorized():
    # 1. Login to get token
    login_res = client.post("/auth/login", data={"username": "testuser", "password": "secretpassword"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create competition
    comp_res = client.post("/competitions/", json={"name": "Winter Tournament"}, headers=headers)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]
    
    # 3. Join competition
    join_res = client.post(f"/competitions/{comp_id}/join", headers=headers)
    assert join_res.status_code == 200
    assert len(join_res.json()["players"]) == 1
    assert join_res.json()["players"][0]["username"] == "testuser"