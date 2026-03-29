import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import models


async def test_full_matchmaking_lifecycle(test_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup: Create 3 users
    for i in range(1, 4):
        await test_client.post("/auth/signup", json={"username": f"player{i}", "email": f"p{i}@test.com", "password": "pass"})
    
    # Login to get tokens
    t1 = (await test_client.post("/auth/login", data={"username": "player1", "password": "pass"})).json()["access_token"]
    t2 = (await test_client.post("/auth/login", data={"username": "player2", "password": "pass"})).json()["access_token"]
    t3 = (await test_client.post("/auth/login", data={"username": "player3", "password": "pass"})).json()["access_token"]
    
    # 2. Create and Join Competition
    comp_res = await test_client.post("/competitions/", json={"name": "Spring Robin"}, headers={"Authorization": f"Bearer {t1}"})
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]
    
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {t1}"})
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {t2}"})
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {t3}"})
    
    # 3. Generate Matches
    gen_res = await test_client.post(f"/competitions/{comp_id}/generate-matches", headers={"Authorization": f"Bearer {t1}"})
    assert gen_res.status_code == 200
    assert gen_res.json()["message"] == "Generated 3 matches"
    
    # 4. Query DB to get the specific match IDs
    result = await db_session.execute(select(models.Match).where(models.Match.competition_id == comp_id).order_by(models.Match.id))
    matches = result.scalars().all()
    assert len(matches) == 3
    
    m1, m2, m3 = matches
    
    # 5. Update Results
    await test_client.put(f"/matches/{m1.id}", json={"result": "1-0"})
    await test_client.put(f"/matches/{m2.id}", json={"result": "1/2-1/2"})
    await test_client.put(f"/matches/{m3.id}", json={"result": "0-1"})
    
    # 6. Fetch Standings
    stand_res = await test_client.get(f"/competitions/{comp_id}/standings")
    assert stand_res.status_code == 200
    standings = stand_res.json()
    
    assert len(standings) == 3
    assert standings[0]["points"] == 1.5
    assert standings[1]["points"] == 1.5
    
    # Verify player2 is in last place with 0 points
    assert standings[2]["points"] == 0.0
    assert standings[2]["player"]["username"] == "player2"