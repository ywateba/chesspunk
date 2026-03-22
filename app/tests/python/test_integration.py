import sys
import os


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from routers.main import app
from core.db.database import Base, get_db
from core.db import models





def test_full_tournament_lifecycle(test_client: TestClient, db_session: Session ):
    # 1. Create Users
    test_client.post("/auth/signup", json={"username": "alice", "email": "alice@test.com", "password": "pass"})
    test_client.post("/auth/signup", json={"username": "bob", "email": "bob@test.com", "password": "pass"})

    # 2. Login Users
    token_alice = test_client.post("/auth/login", data={"username": "alice", "password": "pass"}).json()["access_token"]
    token_bob = test_client.post("/auth/login", data={"username": "bob", "password": "pass"}).json()["access_token"]

    auth_alice = {"Authorization": f"Bearer {token_alice}"}
    auth_bob = {"Authorization": f"Bearer {token_bob}"}

    # 3. Create Competition (Alice creates)
    comp_res = test_client.post("/competitions/", json={"name": "Grand Championship"}, headers=auth_alice)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]

    # 4. Join Competition
    test_client.post(f"/competitions/{comp_id}/join", headers=auth_alice)
    test_client.post(f"/competitions/{comp_id}/join", headers=auth_bob)

    # 5. Start/Generate Matches
    gen_res = test_client.post(f"/competitions/{comp_id}/generate-matches", headers=auth_alice)
    assert gen_res.status_code == 200
    assert "Generated 1 matches" in gen_res.json()["message"]

    # Retrieve match ID
   
    matches = db_session.query(models.Match).filter(models.Match.competition_id == comp_id).all()
    assert len(matches) == 1
    match_id = matches[0].id

    # 6. Play Match & Submit Result
    res_submit = test_client.put(f"/matches/{match_id}", json={"result": "1-0", "pgn_blueprint": "1. e4 e5"}, headers=auth_alice)
    assert res_submit.status_code == 200

    # 7. Check Standings
    stand_res = test_client.get(f"/competitions/{comp_id}/standings")
    assert stand_res.status_code == 200
    assert stand_res.json()[0]["player"]["username"] == "alice"
    assert stand_res.json()[0]["points"] == 1.0