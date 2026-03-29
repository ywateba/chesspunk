from fastapi import HTTPException
from core.schemas import schemas
from core.repositories.base import MatchRepository

async def update_match_result(match_repo: MatchRepository, match_id: int, match_data: schemas.MatchUpdate):
    match = await match_repo.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return await match_repo.update_match(match, result=match_data.result, pgn_blueprint=match_data.pgn_blueprint)
