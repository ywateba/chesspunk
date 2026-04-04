import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import models

async def test_full_tournament_lifecycle(test_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Users
    await test_client.post("/auth/signup", json={"username": "alice", "email": "alice@test.com", "password": "pass"})
    await test_client.post("/auth/signup", json={"username": "bob", "email": "bob@test.com", "password": "pass"})

    res = await db_session.execute(select(models.User).where(models.User.username == "alice"))
    u = res.scalars().first()
    u.role = "organizer"
    await db_session.commit()

    # 2. Login Users
    token_alice = (await test_client.post("/auth/login", data={"username": "alice", "password": "pass"})).json()["access_token"]
    token_bob = (await test_client.post("/auth/login", data={"username": "bob", "password": "pass"})).json()["access_token"]

    auth_alice = {"Authorization": f"Bearer {token_alice}"}
    auth_bob = {"Authorization": f"Bearer {token_bob}"}

    # 3. Create Competition (Alice creates)
    comp_res = await test_client.post("/competitions/", json={"name": "Grand Championship"}, headers=auth_alice)
    assert comp_res.status_code == 200
    comp_id = comp_res.json()["id"]

    # 4. Join Competition
    await test_client.post(f"/competitions/{comp_id}/join", headers=auth_alice)
    await test_client.post(f"/competitions/{comp_id}/join", headers=auth_bob)

    # 5. Start/Generate Matches
    gen_res = await test_client.post(f"/competitions/{comp_id}/generate-matches", headers=auth_alice)
    assert gen_res.status_code == 200
    assert "Generated 1 matches" in gen_res.json()["message"]

    # Retrieve match ID
    result = await db_session.execute(select(models.Match).where(models.Match.competition_id == comp_id))
    matches = result.scalars().all()
    assert len(matches) == 1
    match_id = matches[0].id

    # 6. Play Match & Submit Result
    res_submit = await test_client.put(f"/matches/{match_id}", json={"result": "1-0", "pgn_blueprint": "1. e4 e5"}, headers=auth_alice)
    assert res_submit.status_code == 200

    # 7. Check Standings
    stand_res = await test_client.get(f"/competitions/{comp_id}/standings")
    assert stand_res.status_code == 200
    assert stand_res.json()[0]["player"]["username"] == "alice"
    assert stand_res.json()[0]["points"] == 1.0