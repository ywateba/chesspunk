"""
Authentication Service
======================
Business layer isolating authentication protocols, password security natively,
and user registry tracking abstracted securely behind repositories.
"""

from core.schemas import schemas
from core.auth.utils import verify_password, get_password_hash
from core.db import models
from typing import Optional
from core.repositories.base import UserRepository

async def get_user_by_email_or_username(user_repo: UserRepository, identifier: str) -> Optional[models.User]:
    """
    Resolve a user identity allowing login either via username or primary email.
    """
    user = await user_repo.get_user_by_email(identifier)
    if not user:
        user = await user_repo.get_user_by_username(identifier)
    return user

async def create_user(user_repo: UserRepository, user: schemas.UserCreate) -> models.User:
    """
    Generate standard PBKDF2 hash signatures natively before allocating accounts
    into persistence arrays securely via bounded schemas.
    """
    hashed_password = get_password_hash(user.password)
    return await user_repo.create_user(user, hashed_password)

async def authenticate_user(user_repo: UserRepository, username: str, password: str) -> Optional[models.User]:
    """
    Evaluate structural identities against hashed targets guaranteeing
    secure credential validations safely across identical dependency structures.
    """
    user = await get_user_by_email_or_username(user_repo, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
