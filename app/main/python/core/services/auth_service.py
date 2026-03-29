from core.schemas import schemas
from core.auth.utils import verify_password, get_password_hash
from core.db import models
from typing import Optional
from core.repositories.base import UserRepository

async def get_user_by_email_or_username(user_repo: UserRepository, identifier: str) -> Optional[models.User]:
    user = await user_repo.get_user_by_email(identifier)
    if not user:
        user = await user_repo.get_user_by_username(identifier)
    return user

async def create_user(user_repo: UserRepository, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    return await user_repo.create_user(user, hashed_password)

async def authenticate_user(user_repo: UserRepository, username: str, password: str) -> Optional[models.User]:
    user = await get_user_by_email_or_username(user_repo, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
