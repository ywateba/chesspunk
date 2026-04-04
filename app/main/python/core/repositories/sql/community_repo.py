"""
SQL Community Repository
========================
Persists structural social elements onto PostgreSQL natively managing identical models.
"""

from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from core.repositories.base import CommunityRepository
from core.schemas import schemas
from core.db import models

class SQLCommunityRepository(CommunityRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_community(self, comm: schemas.CommunityCreate, owner_id: int) -> models.Community:
        db_comm = models.Community(**comm.model_dump(), owner_id=owner_id)
        self.db.add(db_comm)
        await self.db.commit()
        await self.db.refresh(db_comm)
        
        # Add owner automatically initializing graph
        await self.join_community(db_comm.id, owner_id, role="owner")
        return await self.get_community(db_comm.id)

    async def get_community(self, community_id: Any) -> Optional[models.Community]:
        result = await self.db.execute(
            select(models.Community)
            .options(selectinload(models.Community.members))
            .filter(models.Community.id == int(community_id))
        )
        return result.scalars().first()

    async def get_communities(self, skip: int = 0, limit: int = 100) -> List[models.Community]:
        result = await self.db.execute(select(models.Community).offset(skip).limit(limit))
        return result.scalars().all()

    async def join_community(self, community_id: Any, user_id: Any, role: str = "member") -> models.CommunityMember:
        member = models.CommunityMember(community_id=int(community_id), user_id=int(user_id), role=role)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_members(self, community_id: Any) -> List[models.CommunityMember]:
        result = await self.db.execute(select(models.CommunityMember).filter(models.CommunityMember.community_id == int(community_id)))
        return result.scalars().all()
