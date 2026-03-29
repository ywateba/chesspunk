import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from core.services import user_service, competition_service, match_service, auth_service
from core.schemas import schemas

async def test_auth_service(db_session: AsyncSession):
    user_in = schemas.UserCreate(username="svc_user", email="svc@test.com", password="pwd")
    user = await auth_service.create_user(db_session, user_in)
    assert user.id is not None
    
    auth_user = await auth_service.authenticate_user(db_session, "svc_user", "pwd")
    assert auth_user is not None
    assert auth_user.username == "svc_user"
    
    assert await auth_service.authenticate_user(db_session, "svc_user", "wrong") is None

async def test_competition_service(db_session: AsyncSession):
    user_in1 = schemas.UserCreate(username="c1", email="c1@test.com", password="pwd")
    user_in2 = schemas.UserCreate(username="c2", email="c2@test.com", password="pwd")
    user1 = await auth_service.create_user(db_session, user_in1)
    user2 = await auth_service.create_user(db_session, user_in2)
    
    comp_in = schemas.CompetitionCreate(name="SVC Tourney")
    comp = await competition_service.create_competition(db_session, comp_in)
    assert comp.id is not None
    
    await competition_service.join_competition(db_session, comp.id, user1)
    await competition_service.join_competition(db_session, comp.id, user2)
    
    await competition_service.generate_matches(db_session, comp.id)
    
    from sqlalchemy.future import select
    from core.db import models
    result = await db_session.execute(select(models.Match).where(models.Match.competition_id == comp.id))
    matches = result.scalars().all()
    assert len(matches) == 1
    
    match = matches[0]
    await match_service.update_match_result(db_session, match.id, schemas.MatchUpdate(result="1-0"))
    
    db_session.expunge_all()
    
    standings = await competition_service.get_standings(db_session, comp.id)
    assert len(standings) == 2
    assert standings[0]["points"] == 1.0 # Winner gets 1 point
    
async def test_user_service(db_session: AsyncSession):
    await auth_service.create_user(db_session, schemas.UserCreate(username="u1", email="u1@x.com", password="x"))
    users = await user_service.get_users_list(db_session)
    assert len(users) >= 1

async def test_competition_not_found(db_session: AsyncSession):
    with pytest.raises(HTTPException) as excinfo:
        await competition_service.get_competition(db_session, 999)
    assert excinfo.value.status_code == 404

async def test_generate_matches_not_enough_players(db_session: AsyncSession):
    comp_in = schemas.CompetitionCreate(name="Lonely Tourney")
    comp = await competition_service.create_competition(db_session, comp_in)
    with pytest.raises(HTTPException) as excinfo:
        await competition_service.generate_matches(db_session, comp.id)
    assert excinfo.value.status_code == 400

async def test_match_not_found(db_session: AsyncSession):
    with pytest.raises(HTTPException) as excinfo:
        await match_service.update_match_result(db_session, 999, schemas.MatchUpdate(result="1-0"))
    assert excinfo.value.status_code == 404
