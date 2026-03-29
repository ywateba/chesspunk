"""
Users Router
============
Provides endpoints for retrieving user profile data and scanning registries.
"""

from fastapi import APIRouter, Depends
from typing import List

from core.schemas import schemas
from core.auth.utils import get_current_user
from core.db import models
from core.dependencies import get_user_repository
from core.repositories.base import UserRepository
from core.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user safely verified through tokens.
    """
    return current_user

@router.get("/", response_model=List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, user_repo: UserRepository = Depends(get_user_repository)):
    """
    Retrieve a paginated list of all users registered in the repository databases.
    """
    return await user_service.get_users_list(user_repo, skip=skip, limit=limit)