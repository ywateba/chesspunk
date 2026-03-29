from sqlalchemy.orm import Session
from fastapi import HTTPException
from core.db.crud import matches as matches_crud
from core.schemas import schemas

def update_match_result(db: Session, match_id: int, match_data: schemas.MatchUpdate):
    match = matches_crud.get_match(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return matches_crud.update_match(db, match, result=match_data.result, pgn_blueprint=match_data.pgn_blueprint)
