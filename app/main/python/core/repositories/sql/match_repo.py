"""
SQL Match Repository
====================
Updates and logs individual Match outputs explicitly bounded inside SQLAlchemy parameters reliably.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.repositories.base import MatchRepository
from core.schemas import schemas
from core.db import models

class SQLMatchRepository(MatchRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_match(self, match_id: int) -> Optional[models.Match]:
        """
        Pull exact Match execution states inherently mapping unique execution queries.
        """
        result = await self.db.execute(select(models.Match).filter(models.Match.id == match_id))
        return result.scalars().first()

    async def create_matches(self, matches: List[models.Match]) -> List[models.Match]:
        """
        Injects natively array lists simultaneously into persistence layers structurally via optimized batch actions.
        """
        self.db.add_all(matches)
        await self.db.commit()
        for match in matches:
            await self.db.refresh(match)
        return matches

    async def update_match(self, db_match: models.Match, result: str, pgn_blueprint: str = None) -> models.Match:
        """
        Updates logic states committing result schemas universally directly into bounded contexts explicitly.
        """
        db_match.result = result
        if pgn_blueprint:
            db_match.pgn_blueprint = pgn_blueprint
            
        await self.db.commit()
        await self.db.refresh(db_match)
        return db_match
