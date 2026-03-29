import pytest
from sqlalchemy.orm import Session
from core.db.crud import users, competitions, matches
from core.schemas import schemas
from core.db import models

def test_crud_user(db_session: Session):
    user_in = schemas.UserCreate(username="crud_user", email="crud@test.com", password="pwd")
    user = users.create_user(db_session, user_in, "hashed")
    assert user.id is not None
    assert user.username == "crud_user"
    
    fetched = users.get_user_by_email(db_session, "crud@test.com")
    assert fetched.id == user.id
    
    fetched_by_name = users.get_user_by_username(db_session, "crud_user")
    assert fetched_by_name.id == user.id

def test_crud_competition(db_session: Session):
    comp_in = schemas.CompetitionCreate(name="CRUD Tourney")
    comp = competitions.create_competition(db_session, comp_in)
    assert comp.name == "CRUD Tourney"
    
    fetched = competitions.get_competition(db_session, comp.id)
    assert fetched.id == comp.id

def test_crud_match(db_session: Session):
    comp_in = schemas.CompetitionCreate(name="Match Tourney")
    comp = competitions.create_competition(db_session, comp_in)
    
    user1 = users.create_user(db_session, schemas.UserCreate(username="p1", email="p1@x.com", password="x"), "h")
    user2 = users.create_user(db_session, schemas.UserCreate(username="p2", email="p2@x.com", password="x"), "h")
    
    match = models.Match(competition_id=comp.id, white_player_id=user1.id, black_player_id=user2.id)
    created = matches.create_matches(db_session, [match])
    assert len(created) == 1
    
    updated = matches.update_match(db_session, created[0], "1-0", "1. e4")
    assert updated.result == "1-0"
    assert updated.pgn_blueprint == "1. e4"

def test_crud_get_user_by_id(db_session: Session):
    user_in = schemas.UserCreate(username="id_user", email="id@test.com", password="pwd")
    user = users.create_user(db_session, user_in, "hashed")
    fetched = users.get_user(db_session, user.id)
    assert fetched is not None
    assert fetched.username == "id_user"
