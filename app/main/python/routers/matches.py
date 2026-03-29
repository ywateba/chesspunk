from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.schemas import schemas
from core.db.database import get_db
from core.services import match_service

router = APIRouter(prefix="/matches", tags=["matches"])

@router.put("/{match_id}", response_model=schemas.Match)
def update_match_result(match_id: int, match_data: schemas.MatchUpdate, db: Session = Depends(get_db)):
    return match_service.update_match_result(db, match_id, match_data)