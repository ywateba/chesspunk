"""
SQL Social Repository
=====================
Relational storage abstractions handling Post and Comment topologies identically explicitly.
"""
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.repositories.base import SocialRepository
from core.db import models

class SQLSocialRepository(SocialRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_post(self, community_id: Any, author_id: Any, content: str) -> models.Post:
        post = models.Post(community_id=int(community_id), author_id=int(author_id), content=content)
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def get_posts(self, community_id: Any, skip: int = 0, limit: int = 50) -> List[models.Post]:
        result = await self.db.execute(
            select(models.Post).filter(models.Post.community_id == int(community_id))
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_comment(self, entity_type: str, entity_id: Any, author_id: Any, content: str) -> models.Comment:
        comment = models.Comment(
            entity_type=entity_type, entity_id=int(entity_id), 
            author_id=int(author_id), content=content
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_comments(self, entity_type: str, entity_id: Any, skip: int = 0, limit: int = 50) -> List[models.Comment]:
        result = await self.db.execute(
            select(models.Comment)
            .filter(models.Comment.entity_type == entity_type, models.Comment.entity_id == int(entity_id))
            .offset(skip).limit(limit)
        )
        return result.scalars().all()
