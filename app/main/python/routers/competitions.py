from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.schemas import schemas
from core.auth.utils import get_current_user
from core.db import models
from core.db.database import get_db
from core.services import competition_service


router = APIRouter(prefix="/competitions", tags=["competitions"])

@router.get("/", response_model=List[schemas.Competition])
def read_competitions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return competition_service.get_competitions(db, skip=skip, limit=limit)

@router.get("/{competition_id}", response_model=schemas.Competition)
def read_competition(competition_id: int, db: Session = Depends(get_db)):
    return competition_service.get_competition(db, competition_id)

@router.post("/", response_model=schemas.Competition)
def create_competition(comp: schemas.CompetitionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return competition_service.create_competition(db, comp)

@router.post("/{competition_id}/join", response_model=schemas.Competition)
def join_competition(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return competition_service.join_competition(db, competition_id, current_user)

@router.get("/{competition_id}/standings", response_model=List[schemas.PlayerStanding])
def get_standings(competition_id: int, db: Session = Depends(get_db)):
    return competition_service.get_standings(db, competition_id)

@router.post("/{competition_id}/generate-matches")
def generate_matches(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return competition_service.generate_matches(db, competition_id)