import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.db.database import get_db

from core.repositories.base import UserRepository, CompetitionRepository, MatchRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.match_repo import SQLMatchRepository

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "SQL":
        return SQLUserRepository(db)
    # Add NoSQL fallback return routines here natively upon scaling out
    raise NotImplementedError("NoSQL repository is not implemented yet")

def get_competition_repository(db: AsyncSession = Depends(get_db)) -> CompetitionRepository:
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "SQL":
        return SQLCompetitionRepository(db)
    raise NotImplementedError("NoSQL repository is not implemented yet")

def get_match_repository(db: AsyncSession = Depends(get_db)) -> MatchRepository:
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "SQL":
        return SQLMatchRepository(db)
    raise NotImplementedError("NoSQL repository is not implemented yet")
