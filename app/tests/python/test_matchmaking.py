import sys
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


from routers.main import app
from core.db.database import Base, get_db
from core.db import models




# --- Tests ---

def test_full_matchmaking_lifecycle(test_client: TestClient, db_session: Session):
    # 1. Setup: Create 3 users
    for i in range(1, 4):
        test_client.post("/auth/signup", json={"username": f"player{i}", "email": f"p{i}@test.com", "password": "pass"})
    
    # Login to get tokens
    t1 = test_client.post("/auth/login", data={"username": "player1", "password": "pass"}).json()["access_token"]
    t2 = test_client.post("/auth/login", data={"username": "player2", "password": "pass"}).json()["access_token"]
    t3 = test_client.post("/auth/login", data={"username": "player3", "password": "pass"}).json()["access_token"]
    
    # 2. Create and Join Competition
    comp_res = test_client.post("/competitions/", json={"name": "Spring Robin"}, headers={"Authorization": f"Bearer {t1}"})
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]
    
    test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {t1}"})
    test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {t2}"})
    test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {t3}"})
    
    # 3. Generate Matches
    gen_res = test_client.post(f"/competitions/{comp_id}/generate-matches", headers={"Authorization": f"Bearer {t1}"})
    assert gen_res.status_code == 200
    assert gen_res.json()["message"] == "Generated 3 matches"
    
    # 4. Query DB to get the specific match IDs
  
    matches = db_session.query(models.Match).filter(models.Match.competition_id == comp_id).order_by(models.Match.id).all()
    assert len(matches) == 3
    
    m1, m2, m3 = matches
    # Based on the iteration order in main.py:
    # m1: player1 (W) vs player2 (B)
    # m2: player1 (W) vs player3 (B)
    # m3: player2 (W) vs player3 (B)
    
    # 5. Update Results
    # player1 beats player2 (1 pt to p1)
    test_client.put(f"/matches/{m1.id}", json={"result": "1-0"})
    # player1 draws player3 (0.5 pt to p1, 0.5 pt to p3)
    test_client.put(f"/matches/{m2.id}", json={"result": "1/2-1/2"})
    # player3 beats player2 (Black wins, 1 pt to p3)
    test_client.put(f"/matches/{m3.id}", json={"result": "0-1"})
    
    # 6. Fetch Standings
    stand_res = test_client.get(f"/competitions/{comp_id}/standings")
    assert stand_res.status_code == 200
    standings = stand_res.json()
    
    assert len(standings) == 3
    
    # player1: 1 win, 1 draw -> 1.5 pts
    # player3: 1 win, 1 draw -> 1.5 pts
    # player2: 0 wins -> 0 pts
    assert standings[0]["points"] == 1.5
    assert standings[1]["points"] == 1.5
    
    # Verify player2 is in last place with 0 points
    assert standings[2]["points"] == 0.0
    assert standings[2]["player"]["username"] == "player2"
    
  