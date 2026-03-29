from fastapi import APIRouter, Depends
from typing import List

from core.schemas import schemas
from core.auth.utils import get_current_user
from core.db import models
from core.dependencies import get_competition_repository, get_match_repository
from core.repositories.base import CompetitionRepository, MatchRepository
from core.services import competition_service


router = APIRouter(prefix="/competitions", tags=["competitions"])

@router.get("/", response_model=List[schemas.Competition])
async def read_competitions(skip: int = 0, limit: int = 100, comp_repo: CompetitionRepository = Depends(get_competition_repository)):
    return await competition_service.get_competitions(comp_repo, skip=skip, limit=limit)

@router.get("/{competition_id}", response_model=schemas.Competition)
async def read_competition(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository)):
    return await competition_service.get_competition(comp_repo, competition_id)

@router.post("/", response_model=schemas.Competition)
async def create_competition(comp: schemas.CompetitionCreate, comp_repo: CompetitionRepository = Depends(get_competition_repository), current_user: models.User = Depends(get_current_user)):
    return await competition_service.create_competition(comp_repo, comp)

@router.post("/{competition_id}/join", response_model=schemas.Competition)
async def join_competition(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository), current_user: models.User = Depends(get_current_user)):
    return await competition_service.join_competition(comp_repo, competition_id, current_user)

@router.get("/{competition_id}/standings", response_model=List[schemas.PlayerStanding])
async def get_standings(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository)):
    return await competition_service.get_standings(comp_repo, competition_id)

@router.post("/{competition_id}/generate-matches")
async def generate_matches(competition_id: int, comp_repo: CompetitionRepository = Depends(get_competition_repository), match_repo: MatchRepository = Depends(get_match_repository), current_user: models.User = Depends(get_current_user)):
    return await competition_service.generate_matches(comp_repo, match_repo, competition_id)