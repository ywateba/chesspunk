"""
Dependency Injection Framework
==============================
Yields repository instantiations mapping application executions to SQL
or NoSQL environments dynamically based upon the active deployment strategy.
"""

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
    """
    Dependency provider evaluating active User tracking engines exclusively.
    Yields native MongoDB collections if configured, otherwise falls back to PostgreSQL securely.
    """
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoUserRepository() # Beanie documents act universally across the application framework inherently
    return SQLUserRepository(db)

def get_competition_repository(db: AsyncSession = Depends(get_db)) -> CompetitionRepository:
    """
    Dependency provider evaluating active Competition tracking engines exclusively.
    Yields identical native abstract protocols regardless of deployment architectures.
    """
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoCompetitionRepository()
    return SQLCompetitionRepository(db)

def get_match_repository(db: AsyncSession = Depends(get_db)) -> MatchRepository:
    """
    Dependency provider evaluating active Match tracking engines explicitly routing topologies.
    """
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoMatchRepository()
    return SQLMatchRepository(db)
