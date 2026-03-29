from fastapi import APIRouter, Depends

from core.schemas import schemas
from core.dependencies import get_match_repository
from core.repositories.base import MatchRepository
from core.services import match_service

router = APIRouter(prefix="/matches", tags=["matches"])

@router.put("/{match_id}", response_model=schemas.Match)
async def update_match_result(match_id: int, match_data: schemas.MatchUpdate, match_repo: MatchRepository = Depends(get_match_repository)):
    return await match_service.update_match_result(match_repo, match_id, match_data)