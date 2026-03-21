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
import models

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

def test_full_tournament_lifecycle():
    # 1. Create Users
    client.post("/auth/signup", json={"username": "alice", "email": "alice@test.com", "password": "pass"})
    client.post("/auth/signup", json={"username": "bob", "email": "bob@test.com", "password": "pass"})

    # 2. Login Users
    token_alice = client.post("/auth/login", data={"username": "alice", "password": "pass"}).json()["access_token"]
    token_bob = client.post("/auth/login", data={"username": "bob", "password": "pass"}).json()["access_token"]

    auth_alice = {"Authorization": f"Bearer {token_alice}"}
    auth_bob = {"Authorization": f"Bearer {token_bob}"}

    # 3. Create Competition (Alice creates)
    comp_res = client.post("/competitions/", json={"name": "Grand Championship"}, headers=auth_alice)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]

    # 4. Join Competition
    client.post(f"/competitions/{comp_id}/join", headers=auth_alice)
    client.post(f"/competitions/{comp_id}/join", headers=auth_bob)

    # 5. Start/Generate Matches
    gen_res = client.post(f"/competitions/{comp_id}/generate-matches", headers=auth_alice)
    assert gen_res.status_code == 200
    assert "Generated 1 matches" in gen_res.json()["message"]

    # Retrieve match ID
    db = TestingSessionLocal()
    matches = db.query(models.Match).filter(models.Match.competition_id == comp_id).all()
    assert len(matches) == 1
    match_id = matches[0].id

    # 6. Play Match & Submit Result
    res_submit = client.put(f"/matches/{match_id}", json={"result": "1-0", "pgn_blueprint": "1. e4 e5"}, headers=auth_alice)
    assert res_submit.status_code == 200

    # 7. Check Standings
    stand_res = client.get(f"/competitions/{comp_id}/standings")
    assert stand_res.status_code == 200
    assert stand_res.json()[0]["player"]["username"] == "alice"
    assert stand_res.json()[0]["points"] == 1.0