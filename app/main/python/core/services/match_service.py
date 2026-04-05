"""
Match Service
=============
Allows standard update patches routing securely to the match repositories mapping validation behaviors dynamically.
"""

from fastapi import HTTPException
from core.schemas import schemas
from core.repositories.base import MatchRepository
from core.services.chess_service import evaluate_pgn_with_stockfish

async def update_match_result(match_repo: MatchRepository, match_id: str, match_data: schemas.MatchUpdate):
    """
    Submits game resolutions including valid FIDE chess notations explicitly updating
    the overarching leaderboard constraints seamlessly tracking 404 targets.
    """
    match = await match_repo.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return await match_repo.update_match(match, result=match_data.result, pgn_blueprint=match_data.pgn_blueprint)

async def evaluate_match(match_repo: MatchRepository, match_id: str, time_limit_ms: int = 50):
    """
    Evaluates a completed match using Stockfish via the match's stored PGN blueprint.
    Returns a normalized evaluation payload or raises 404 when the match is missing or lacks PGN.
    """
    match = await match_repo.get_match(match_id)
    if not match or not match.pgn_blueprint:
        raise HTTPException(status_code=404, detail="Match not found or PGN blueprint is missing.")

    evaluation = await evaluate_pgn_with_stockfish(match.pgn_blueprint, time_limit_ms=time_limit_ms)
    return {"match_id": match_id, "evaluation": evaluation}
