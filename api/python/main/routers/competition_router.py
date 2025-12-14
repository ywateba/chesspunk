from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.schemas import competition_schema
from db import crud
from db.database import get_db

router = APIRouter(
    prefix="/competitions",
    tags=["competitions"]
)

@router.post("/", response_model=competition_schema.Competition)
def create_competition(comp: competition_schema.CompetitionCreate, db: Session = Depends(get_db)):
    return crud.create_competition(db=db, comp=comp)

@router.get("/", response_model=List[competition_schema.Competition])
def read_competitions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_competitions(db, skip=skip, limit=limit)

@router.get("/{competition_id}", response_model=competition_schema.Competition)
def read_competition(competition_id: int, db: Session = Depends(get_db)):
    db_comp = crud.get_competition(db, competition_id=competition_id)
    if db_comp is None:
        raise HTTPException(status_code=404, detail="Competition not found")
    return db_comp

@router.post("/{competition_id}/join", response_model=competition_schema.Competition)
def join_competition(competition_id: int, user_id: int, db: Session = Depends(get_db)):
    db_comp = crud.join_competition(db, competition_id=competition_id, user_id=user_id)
    if db_comp is None:
        raise HTTPException(status_code=404, detail="Competition or User not found")
    return db_comp

@router.post("/{competition_id}/generate-matches")
def generate_matches(competition_id: int, db: Session = Depends(get_db)):
    matches = crud.generate_matches(db, competition_id=competition_id)
    if matches is None:
        raise HTTPException(status_code=404, detail="Competition not found")
    if matches == "not_enough_players":
        raise HTTPException(status_code=400, detail="Not enough players to generate matches")
    return {"message": f"Generated {len(matches)} matches"}
