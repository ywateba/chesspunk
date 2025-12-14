from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from core.schemas import match_schema
from db import crud
from db.database import get_db

router = APIRouter(
    prefix="/matches",
    tags=["matches"]
)

@router.get("/", response_model=List[match_schema.Match])
def read_matches(skip: int = 0, limit: int = 100, competition_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.get_matches(db, skip=skip, limit=limit, competition_id=competition_id)

@router.put("/{match_id}", response_model=match_schema.Match)
def update_match_result(match_id: int, match_data: match_schema.MatchUpdate, db: Session = Depends(get_db)):
    db_match = crud.update_match(db, match_id=match_id, match_data=match_data)
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return db_match
