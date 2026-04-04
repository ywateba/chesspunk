import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.match_repo import SQLMatchRepository
from core.schemas import schemas
from core.db import models

async def test_crud_user(db_session: AsyncSession):
    user_repo = SQLUserRepository(db_session)
    user_in = schemas.UserCreate(username="crud_user", email="crud@test.com", password="pwd")
    user = await user_repo.create_user(user_in, "hashed")
    assert user.id is not None
    assert user.username == "crud_user"
    
    fetched = await user_repo.get_user_by_email("crud@test.com")
    assert fetched.id == user.id
    
    fetched_by_name = await user_repo.get_user_by_username("crud_user")
    assert fetched_by_name.id == user.id

async def test_crud_competition(db_session: AsyncSession):
    comp_repo = SQLCompetitionRepository(db_session)
    comp_in = schemas.CompetitionCreate(name="CRUD Tourney")
    comp = await comp_repo.create_competition(comp_in)
    assert comp.name == "CRUD Tourney"
    
    fetched = await comp_repo.get_competition(comp.id)
    assert fetched.id == comp.id

async def test_crud_match(db_session: AsyncSession):
    user_repo = SQLUserRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    match_repo = SQLMatchRepository(db_session)
    
    comp_in = schemas.CompetitionCreate(name="Match Tourney")
    comp = await comp_repo.create_competition(comp_in)
    
    user1 = await user_repo.create_user(schemas.UserCreate(username="p1", email="p1@x.com", password="x"), "h")
    user2 = await user_repo.create_user(schemas.UserCreate(username="p2", email="p2@x.com", password="x"), "h")
    
    match = models.Match(competition_id=comp.id, white_player_id=user1.id, black_player_id=user2.id)
    created = await match_repo.create_matches([match])
    assert len(created) == 1
    
    updated = await match_repo.update_match(created[0], "1-0", "1. e4")
    assert updated.result == "1-0"
    assert updated.pgn_blueprint == "1. e4"

async def test_crud_get_user_by_id(db_session: AsyncSession):
    user_repo = SQLUserRepository(db_session)
    user_in = schemas.UserCreate(username="id_user", email="id@test.com", password="pwd")
    user = await user_repo.create_user(user_in, "hashed")
    fetched = await user_repo.get_user(user.id)
    assert fetched is not None
    assert fetched.username == "id_user"
