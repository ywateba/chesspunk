"""
Matches Router
==============
Handles individual chess match updates including results and PGN uploads.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File

from core.schemas import schemas
from core.auth.utils import get_current_user, RoleChecker
from core.db import models
from core.dependencies import get_match_repository
from core.repositories.base import MatchRepository
from core.services.match_service import update_match_result as service_update_match_result
from core.services.chess_service import parse_bulk_pgn, evaluate_pgn_with_stockfish
from core.rate_limit import limiter

router = APIRouter(prefix="/matches", tags=["matches"])

@router.put("/{match_id}", response_model=schemas.Match, summary="Update match result")
async def update_match_result(match_id: int, match_data: schemas.MatchUpdate, match_repo: MatchRepository = Depends(get_match_repository), current_user: models.User = Depends(RoleChecker(["admin", "organizer"]))):
    """
    Updates the outcome of a match and attaches optional PGN blueprints simulating raw match persistence operations.
    Matches are typically generated securely through the Competition routers directly natively.
    """
    return await service_update_match_result(match_repo, match_id, match_data)

@router.post("/bulk-upload", summary="Bulk upload PGN match datasets")
@limiter.limit("5/minute")
async def upload_pgn(request: Request, file: UploadFile = File(...), current_user: models.User = Depends(RoleChecker(["admin", "organizer"]))):
    """
    Parses unoptimized multi-game PGN strings dynamically saving raw chess footprints.
    """
    content = await file.read()
    pgn_string = content.decode("utf-8")
    parsed_games = await parse_bulk_pgn(pgn_string)
    
    return {
        "message": f"Successfully parsed {len(parsed_games)} games",
        "games_metadata": [{"event": g["headers"].get("Event", "?"), "white": g["headers"].get("White", "?"), "black": g["headers"].get("Black", "?")} for g in parsed_games]
    }

@router.post("/{match_id}/evaluate", summary="Evaluate full match with Stockfish")
@limiter.limit("5/minute")
async def evaluate_match(request: Request, match_id: int, match_repo: MatchRepository = Depends(get_match_repository), current_user: models.User = Depends(get_current_user)):
    """
    Spawns Stockfish microservice processes locally assigning blunder metrics asynchronously.
    """
    match = await match_repo.get_match(match_id)
    if not match or not match.pgn_blueprint:
        raise HTTPException(status_code=404, detail="Match not found or PGN blueprint is missing.")
        
    evaluation = await evaluate_pgn_with_stockfish(match.pgn_blueprint, time_limit_ms=50)
    return {"match_id": match_id, "evaluation": evaluation}