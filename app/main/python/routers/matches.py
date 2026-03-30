"""
Matches Router
==============
Handles individual chess match updates including results and PGN uploads.
"""

from fastapi import APIRouter, Depends

from core.schemas import schemas
from core.dependencies import get_match_repository
from core.repositories.base import MatchRepository
from core.services import match_service
from core.auth.utils import RoleChecker
from core.db import models

router = APIRouter(prefix="/matches", tags=["matches"])

@router.put("/{match_id}", response_model=schemas.Match, summary="Update match result")
async def update_match_result(match_id: int, match_data: schemas.MatchUpdate, match_repo: MatchRepository = Depends(get_match_repository), current_user: models.User = Depends(RoleChecker(["admin", "organizer"]))):
    """
    Updates the outcome of a match and attaches optional PGN blueprints simulating raw match persistence operations.
    Matches are typically generated securely through the Competition routers directly natively.
    """
    return await match_service.update_match_result(match_repo, match_id, match_data)