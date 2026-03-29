"""
Match Service
=============
Allows standard update patches routing securely to the match repositories mapping validation behaviors dynamically.
"""

from fastapi import HTTPException
from core.schemas import schemas
from core.repositories.base import MatchRepository

async def update_match_result(match_repo: MatchRepository, match_id: int, match_data: schemas.MatchUpdate):
    """
    Submits game resolutions including valid FIDE chess notations explicitly updating
    the overarching leaderboard constraints seamlessly tracking 404 targets.
    """
    match = await match_repo.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return await match_repo.update_match(match, result=match_data.result, pgn_blueprint=match_data.pgn_blueprint)
