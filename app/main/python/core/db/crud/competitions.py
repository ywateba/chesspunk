from sqlalchemy.orm import Session
from core.db import models
from core.schemas import schemas

def get_competition(db: Session, competition_id: int):
    return db.query(models.Competition).filter(models.Competition.id == competition_id).first()

def get_competitions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Competition).offset(skip).limit(limit).all()

def create_competition(db: Session, comp: schemas.CompetitionCreate):
    db_comp = models.Competition(name=comp.name)
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

def add_player_to_competition(db: Session, db_comp: models.Competition, user: models.User):
    if user not in db_comp.players:
        db_comp.players.append(user)
        db.commit()
        db.refresh(db_comp)
    return db_comp

def update_competition_status(db: Session, db_comp: models.Competition, status: str):
    db_comp.status = status
    db.commit()
    db.refresh(db_comp)
    return db_comp
