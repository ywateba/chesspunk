from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from core.db import models
from core.schemas import schemas

async def get_competition(db: AsyncSession, competition_id: int):
    result = await db.execute(
        select(models.Competition)
        .options(selectinload(models.Competition.players), selectinload(models.Competition.matches))
        .where(models.Competition.id == competition_id)
    )
    return result.scalars().first()

async def get_competitions(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Competition).offset(skip).limit(limit))
    return result.scalars().all()

async def create_competition(db: AsyncSession, comp: schemas.CompetitionCreate):
    db_comp = models.Competition(name=comp.name)
    db.add(db_comp)
    await db.commit()
    return await get_competition(db, db_comp.id)

async def add_player_to_competition(db: AsyncSession, db_comp: models.Competition, user: models.User):
    # Relies on players being loaded via selectinload initially
    if user not in db_comp.players:
        db_comp.players.append(user)
        await db.commit()
    return await get_competition(db, db_comp.id)

async def update_competition_status(db: AsyncSession, db_comp: models.Competition, status: str):
    db_comp.status = status
    await db.commit()
    return await get_competition(db, db_comp.id)
