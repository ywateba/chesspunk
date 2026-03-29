from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from core.db import models
from core.schemas import schemas
from core.repositories.base import CompetitionRepository
from typing import Optional, List, Any

class SQLCompetitionRepository(CompetitionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_competition(self, competition_id: int) -> Optional[models.Competition]:
        result = await self.db.execute(
            select(models.Competition)
            .options(selectinload(models.Competition.players), selectinload(models.Competition.matches))
            .where(models.Competition.id == competition_id)
        )
        return result.scalars().first()

    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[models.Competition]:
        result = await self.db.execute(select(models.Competition).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_competition(self, comp: schemas.CompetitionCreate) -> models.Competition:
        db_comp = models.Competition(name=comp.name)
        self.db.add(db_comp)
        await self.db.commit()
        return await self.get_competition(db_comp.id)

    async def add_player_to_competition(self, db_comp: Any, user: Any) -> models.Competition:
        if user not in db_comp.players:
            db_comp.players.append(user)
            await self.db.commit()
        return await self.get_competition(db_comp.id)

    async def update_competition_status(self, db_comp: Any, status: str) -> models.Competition:
        db_comp.status = status
        await self.db.commit()
        return await self.get_competition(db_comp.id)
