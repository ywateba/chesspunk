import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from core.services import user_service, competition_service, match_service, auth_service
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.match_repo import SQLMatchRepository
from core.schemas import schemas

async def test_auth_service(db_session: AsyncSession):
    user_repo = SQLUserRepository(db_session)
    user_in = schemas.UserCreate(username="svc_user", email="svc@test.com", password="pwd")
    user = await auth_service.create_user(user_repo, user_in)
    assert user.id is not None
    
    auth_user = await auth_service.authenticate_user(user_repo, "svc_user", "pwd")
    assert auth_user is not None
    assert auth_user.username == "svc_user"
    
    assert await auth_service.authenticate_user(user_repo, "svc_user", "wrong") is None

async def test_competition_service(db_session: AsyncSession):
    user_repo = SQLUserRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    match_repo = SQLMatchRepository(db_session)
    
    user_in1 = schemas.UserCreate(username="c1", email="c1@test.com", password="pwd")
    user_in2 = schemas.UserCreate(username="c2", email="c2@test.com", password="pwd")
    user1 = await auth_service.create_user(user_repo, user_in1)
    user2 = await auth_service.create_user(user_repo, user_in2)
    
    comp_in = schemas.CompetitionCreate(name="SVC Tourney")
    comp = await competition_service.create_competition(comp_repo, comp_in)
    assert comp.id is not None
    
    await competition_service.join_competition(comp_repo, comp.id, user1)
    await competition_service.join_competition(comp_repo, comp.id, user2)
    
    await competition_service.generate_matches(comp_repo, match_repo, comp.id)
    
    from sqlalchemy.future import select
    from core.db import models
    result = await db_session.execute(select(models.Match).where(models.Match.competition_id == comp.id))
    matches = result.scalars().all()
    assert len(matches) == 1
    
    match = matches[0]
    await match_service.update_match_result(match_repo, match.id, schemas.MatchUpdate(result="1-0"))
    
    db_session.expunge_all()
    
    standings = await competition_service.get_standings(comp_repo, comp.id)
    assert len(standings) == 2
    assert standings[0]["points"] == 1.0 # Winner gets 1 point
    
async def test_user_service(db_session: AsyncSession):
    user_repo = SQLUserRepository(db_session)
    await auth_service.create_user(user_repo, schemas.UserCreate(username="u1", email="u1@x.com", password="x"))
    users = await user_service.get_users_list(user_repo)
    assert len(users) >= 1

async def test_competition_not_found(db_session: AsyncSession):
    comp_repo = SQLCompetitionRepository(db_session)
    with pytest.raises(HTTPException) as excinfo:
        await competition_service.get_competition(comp_repo, 999)
    assert excinfo.value.status_code == 404

async def test_generate_matches_not_enough_players(db_session: AsyncSession):
    comp_repo = SQLCompetitionRepository(db_session)
    match_repo = SQLMatchRepository(db_session)
    comp_in = schemas.CompetitionCreate(name="Lonely Tourney")
    comp = await competition_service.create_competition(comp_repo, comp_in)
    with pytest.raises(HTTPException) as excinfo:
        await competition_service.generate_matches(comp_repo, match_repo, comp.id)
    assert excinfo.value.status_code == 400

async def test_match_not_found(db_session: AsyncSession):
    match_repo = SQLMatchRepository(db_session)
    with pytest.raises(HTTPException) as excinfo:
        await match_service.update_match_result(match_repo, 999, schemas.MatchUpdate(result="1-0"))
    assert excinfo.value.status_code == 404
