import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.db.database import get_db

from core.repositories.base import UserRepository, CompetitionRepository, MatchRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.match_repo import SQLMatchRepository

from core.repositories.nosql.user_repo import MongoUserRepository
from core.repositories.nosql.competition_repo import MongoCompetitionRepository
from core.repositories.nosql.match_repo import MongoMatchRepository

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoUserRepository() # Beanie documents act universally across the application framework inherently
    return SQLUserRepository(db)

def get_competition_repository(db: AsyncSession = Depends(get_db)) -> CompetitionRepository:
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoCompetitionRepository()
    return SQLCompetitionRepository(db)

def get_match_repository(db: AsyncSession = Depends(get_db)) -> MatchRepository:
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoMatchRepository()
    return SQLMatchRepository(db)
