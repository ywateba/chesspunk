from sqlalchemy.orm import Session
from db import models
from core import schemas

# --- User CRUD ---

def create_user(db: Session, user: schemas.user_schema.UserCreate):
    db_user = models.User(username=user.username, email=user.email, is_player=user.is_player)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_players(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).filter(models.User.is_player == True).offset(skip).limit(limit).all()

def get_player(db: Session, player_id: int):
    return db.query(models.User).filter(models.User.id == player_id, models.User.is_player == True).first()

# --- Competition CRUD ---

def create_competition(db: Session, comp: schemas.competition_schema.CompetitionCreate):
    db_comp = models.Competition(name=comp.name)
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

def get_competitions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Competition).offset(skip).limit(limit).all()

def get_competition(db: Session, competition_id: int):
    return db.query(models.Competition).filter(models.Competition.id == competition_id).first()

def join_competition(db: Session, competition_id: int, user_id: int):
    db_comp = get_competition(db, competition_id)
    db_user = get_user(db, user_id)
    
    if not db_comp or not db_user:
        return None
    
    db_comp.players.append(db_user)
    db.commit()
    db.refresh(db_comp)
    return db_comp

def generate_matches(db: Session, competition_id: int):
    db_comp = get_competition(db, competition_id)
    if not db_comp:
        return None
    
    players = db_comp.players
    if len(players) < 2:
        return "not_enough_players"

    matches_created = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            new_match = models.Match(
                competition_id=competition_id,
                white_player_id=players[i].id,
                black_player_id=players[j].id,
                result="*"
            )
            db.add(new_match)
            matches_created.append(new_match)
    
    db_comp.status = "active"
    db.commit()
    return matches_created

# --- Match CRUD ---

def get_matches(db: Session, skip: int = 0, limit: int = 100, competition_id: int = None):
    query = db.query(models.Match)
    if competition_id:
        query = query.filter(models.Match.competition_id == competition_id)
    return query.offset(skip).limit(limit).all()

def update_match(db: Session, match_id: int, match_data: schemas.match_schema.MatchUpdate):
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        return None
        
    db_match.result = match_data.result
    if match_data.pgn_blueprint:
        db_match.pgn_blueprint = match_data.pgn_blueprint
        
    db.commit()
    db.refresh(db_match)
    return db_match