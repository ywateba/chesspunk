from sqlalchemy.orm import Session
from core.db import models
from typing import List

def get_match(db: Session, match_id: int):
    return db.query(models.Match).filter(models.Match.id == match_id).first()

def create_matches(db: Session, matches: List[models.Match]):
    db.add_all(matches)
    db.commit()
    return matches

def update_match(db: Session, db_match: models.Match, result: str, pgn_blueprint: str = None):
    db_match.result = result
    if pgn_blueprint:
        db_match.pgn_blueprint = pgn_blueprint
    db.commit()
    db.refresh(db_match)
    return db_match
