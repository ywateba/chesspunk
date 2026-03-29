from sqlalchemy.ext.asyncio import AsyncSession
from core.db.crud import users as users_crud
from core.schemas import schemas
from core.auth.utils import verify_password, get_password_hash
from core.db import models
from typing import Optional

async def get_user_by_email_or_username(db: AsyncSession, identifier: str) -> Optional[models.User]:
    user = await users_crud.get_user_by_email(db, identifier)
    if not user:
        user = await users_crud.get_user_by_username(db, identifier)
    return user

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    return await users_crud.create_user(db, user, hashed_password)

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[models.User]:
    user = await get_user_by_email_or_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
