"""
SQL User Repository
===================
Executes concrete PostgreSQL interactions matching the UserRepository constraints.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.repositories.base import UserRepository
from core.schemas import schemas
from core.db import models

class SQLUserRepository(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[models.User]:
        """
        Retrieves users explicitly via internal Integer IDs.
        """
        result = await self.db.execute(select(models.User).filter(models.User.id == user_id))
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[models.User]:
        """
        Authenticates unique session properties natively comparing targeted emails.
        """
        result = await self.db.execute(select(models.User).filter(models.User.email == email))
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[models.User]:
        """
        Validates username registrations protecting global constraints statically.
        """
        result = await self.db.execute(select(models.User).filter(models.User.username == username))
        return result.scalars().first()

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[models.User]:
        """
        Scans all accounts enforcing paginated blocks efficiently.
        """
        result = await self.db.execute(select(models.User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_user(self, user: schemas.UserCreate, hashed_password: str) -> models.User:
        """
        Commits secure account definitions allocating PostgreSQL primary keys inherently.
        """
        db_user = models.User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
