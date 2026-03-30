"""
Competitions Router
===================
Manages chess tournament lifecycles including player registration, standings,
and match generations securely isolated through dependency repositories.
"""

from fastapi import APIRouter, Depends, Request
from typing import List

from core.schemas import schemas
from core.auth.utils import get_current_user, RoleChecker
from core.db import models
from core.dependencies import get_competition_repository, get_match_repository, get_user_repository
from core.repositories.base import CompetitionRepository, MatchRepository, UserRepository
from core.services import competition_service
from core.rate_limit import limiter


router = APIRouter(prefix="/competitions", tags=["competitions"])

@router.get("/", response_model=List[schemas.Competition])
async def read_competitions(skip: int = 0, limit: int = 100, comp_repo: CompetitionRepository = Depends(get_competition_repository)):
    """
    Retrieve a paginated list of all public competitions.
    """
    return await competition_service.get_competitions(comp_repo, skip=skip, limit=limit)

@router.get("/{competition_id}", response_model=schemas.Competition)
async def read_competition(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository)):
    """
    Retrieve the layout of a specific competition including scheduled matches.
    """
    return await competition_service.get_competition(comp_repo, competition_id)

@router.post("/", response_model=schemas.Competition, summary="Create a competition")
@limiter.limit("5/minute")
async def create_competition(request: Request, comp: schemas.CompetitionCreate, comp_repo: CompetitionRepository = Depends(get_competition_repository), current_user: models.User = Depends(RoleChecker(["admin", "organizer"]))):
    """
    Initialize a new competition strictly requiring an authenticated creator session.
    """
    return await competition_service.create_competition(comp_repo, comp)

@router.post("/{competition_id}/join", response_model=schemas.Competition)
async def join_competition(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository), current_user: models.User = Depends(get_current_user)):
    """
    Registers the authenticated user explicitly into the targeted competition.
    """
    return await competition_service.join_competition(comp_repo, competition_id, current_user)

@router.get("/{competition_id}/standings", response_model=List[schemas.PlayerStanding])
async def get_standings(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository)):
    """
    Calculate real-time leaderboard standings dynamically ranking points and wins.
    """
    return await competition_service.get_standings(comp_repo, competition_id)

@router.post("/{competition_id}/generate-matches", summary="Generate matches")
@limiter.limit("2/minute")
async def generate_matches(request: Request, competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository), match_repo: MatchRepository = Depends(get_match_repository), current_user: models.User = Depends(RoleChecker(["admin", "organizer"]))):
    """
    Locks the competition and seeds a Round Robin matrix scheduling explicit matchups.
    """
    return await competition_service.generate_matches(comp_repo, match_repo, competition_id)

@router.post("/{competition_id}/finish", summary="Finish competition and formulate Elo")
@limiter.limit("2/minute")
async def finish_competition(request: Request, competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository), user_repo: UserRepository = Depends(get_user_repository), current_user: models.User = Depends(RoleChecker(["admin", "organizer"]))):
    """
    Safely terminates actively running tournament lifecycles dynamically allocating mathematically standard algorithmic Elo properties.
    """
    return await competition_service.finish_competition(comp_repo, user_repo, competition_id)