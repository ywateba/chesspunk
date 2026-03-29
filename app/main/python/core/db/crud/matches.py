from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import models
from typing import List

async def get_match(db: AsyncSession, match_id: int):
    result = await db.execute(select(models.Match).where(models.Match.id == match_id))
    return result.scalars().first()

async def create_matches(db: AsyncSession, matches: List[models.Match]):
    db.add_all(matches)
    await db.commit()
    return matches

async def update_match(db: AsyncSession, db_match: models.Match, result: str, pgn_blueprint: str = None):
    db_match.result = result
    if pgn_blueprint:
        db_match.pgn_blueprint = pgn_blueprint
    await db.commit()
    await db.refresh(db_match)
    return db_match
