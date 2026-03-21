from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas
from database import get_db

router = APIRouter(prefix="/matches", tags=["matches"])

@router.put("/{match_id}", response_model=schemas.Match)
def update_match_result(match_id: int, match_data: schemas.MatchUpdate, db: Session = Depends(get_db)):
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    db_match.result = match_data.result
    if match_data.pgn_blueprint:
        db_match.pgn_blueprint = match_data.pgn_blueprint
        
    db.commit()
    db.refresh(db_match)
    return db_match