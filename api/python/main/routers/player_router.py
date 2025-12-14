from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.schemas import user_schema
from db import crud
from db.database import get_db

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

@router.get("/", response_model=List[user_schema.User])
def read_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_players(db, skip=skip, limit=limit)

@router.get("/{player_id}", response_model=user_schema.User)
def read_player(player_id: int, db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
