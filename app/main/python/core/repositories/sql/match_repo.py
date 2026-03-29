from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import models
from core.repositories.base import MatchRepository
from typing import Optional, List, Any

class SQLMatchRepository(MatchRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_match(self, match_id: int) -> Optional[models.Match]:
        result = await self.db.execute(select(models.Match).where(models.Match.id == match_id))
        return result.scalars().first()

    async def create_matches(self, matches: List[Any]) -> List[models.Match]:
        self.db.add_all(matches)
        await self.db.commit()
        return matches

    async def update_match(self, db_match: Any, result: str, pgn_blueprint: str = None) -> models.Match:
        db_match.result = result
        if pgn_blueprint:
            db_match.pgn_blueprint = pgn_blueprint
        await self.db.commit()
        await self.db.refresh(db_match)
        return db_match
