"""
SQL Competition Repository
==========================
Transforms logical Competition routines seamlessly managing many-to-many relationship
junctions executing isolated strictly upon PostgreSQL architectures.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.repositories.base import CompetitionRepository
from core.schemas import schemas
from core.db import models

class SQLCompetitionRepository(CompetitionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_competition(self, competition_id: int) -> Optional[models.Competition]:
        """
        Uses explicit recursive joinedloads dynamically populating relationships.
        Loads nested Array metrics (Matches & Players) automatically via explicit SQLAlchemy configurations.
        """
        query = select(models.Competition).options(
            selectinload(models.Competition.players),
            selectinload(models.Competition.matches)
        ).filter(models.Competition.id == competition_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[models.Competition]:
        """
        Isolate public active tournaments efficiently querying paginated blocks securely.
        """
        result = await self.db.execute(
            select(models.Competition)
            .options(selectinload(models.Competition.players))
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_competition(self, comp: schemas.CompetitionCreate) -> models.Competition:
        """
        Initializes tournament foundations yielding basic internal states independently.
        """
        db_comp = models.Competition(**comp.model_dump())
        self.db.add(db_comp)
        await self.db.commit()
        await self.db.refresh(db_comp)
        return db_comp

    async def add_player_to_competition(self, db_comp: models.Competition, user: models.User) -> models.Competition:
        """
        Populate Junction arrays appending explicitly into the ManyToMany competition mapping schema automatically.
        """
        if user not in db_comp.players:
            db_comp.players.append(user)
            await self.db.commit()
            await self.db.refresh(db_comp)
        return db_comp
        
    async def update_competition_status(self, db_comp: models.Competition, status: str) -> models.Competition:
        """
        Reallocates execution lifecycle states securely controlling dynamic matches tracking (e.g., 'active', 'finished').
        """
        db_comp.status = status
        await self.db.commit()
        await self.db.refresh(db_comp)
        return db_comp
