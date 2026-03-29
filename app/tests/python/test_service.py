import pytest
from sqlalchemy.orm import Session
from core.services import user_service, competition_service, match_service, auth_service
from core.schemas import schemas

def test_auth_service(db_session: Session):
    user_in = schemas.UserCreate(username="svc_user", email="svc@test.com", password="pwd")
    user = auth_service.create_user(db_session, user_in)
    assert user.id is not None
    
    auth_user = auth_service.authenticate_user(db_session, "svc_user", "pwd")
    assert auth_user is not None
    assert auth_user.username == "svc_user"
    
    assert auth_service.authenticate_user(db_session, "svc_user", "wrong") is None

def test_competition_service(db_session: Session):
    user_in1 = schemas.UserCreate(username="c1", email="c1@test.com", password="pwd")
    user_in2 = schemas.UserCreate(username="c2", email="c2@test.com", password="pwd")
    user1 = auth_service.create_user(db_session, user_in1)
    user2 = auth_service.create_user(db_session, user_in2)
    
    comp_in = schemas.CompetitionCreate(name="SVC Tourney")
    comp = competition_service.create_competition(db_session, comp_in)
    assert comp.id is not None
    
    competition_service.join_competition(db_session, comp.id, user1)
    competition_service.join_competition(db_session, comp.id, user2)
    
    competition_service.generate_matches(db_session, comp.id)
    
    auth_comp = competition_service.get_competition(db_session, comp.id)
    assert len(auth_comp.matches) == 1
    
    match = auth_comp.matches[0]
    match_service.update_match_result(db_session, match.id, schemas.MatchUpdate(result="1-0"))
    
    standings = competition_service.get_standings(db_session, comp.id)
    assert len(standings) == 2
    assert standings[0]["points"] == 1.0 # Winner gets 1 point
    
def test_user_service(db_session: Session):
    auth_service.create_user(db_session, schemas.UserCreate(username="u1", email="u1@x.com", password="x"))
    users = user_service.get_users_list(db_session)
    assert len(users) >= 1

from fastapi import HTTPException

def test_competition_not_found(db_session: Session):
    with pytest.raises(HTTPException) as excinfo:
        competition_service.get_competition(db_session, 999)
    assert excinfo.value.status_code == 404

def test_generate_matches_not_enough_players(db_session: Session):
    comp_in = schemas.CompetitionCreate(name="Lonely Tourney")
    comp = competition_service.create_competition(db_session, comp_in)
    with pytest.raises(HTTPException) as excinfo:
        competition_service.generate_matches(db_session, comp.id)
    assert excinfo.value.status_code == 400

def test_match_not_found(db_session: Session):
    with pytest.raises(HTTPException) as excinfo:
        match_service.update_match_result(db_session, 999, schemas.MatchUpdate(result="1-0"))
    assert excinfo.value.status_code == 404
