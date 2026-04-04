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

from core.repositories.base import UserRepository, CompetitionRepository, MatchRepository, CommunityRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.match_repo import SQLMatchRepository
from core.repositories.sql.community_repo import SQLCommunityRepository
from core.repositories.sql.social_repo import SQLSocialRepository
from core.repositories.nosql.user_repo import MongoUserRepository
from core.repositories.nosql.competition_repo import MongoCompetitionRepository
from core.repositories.nosql.match_repo import MongoMatchRepository
from core.repositories.nosql.community_repo import MongoCommunityRepository
from core.repositories.nosql.social_repo import MongoSocialRepository
from core.repositories.base import UserRepository, CompetitionRepository, MatchRepository, CommunityRepository, SocialRepository

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

def get_community_repository(db: AsyncSession = Depends(get_db)) -> CommunityRepository:
    """
    Dependency provider evaluating active Community tracking engines explicitly routing topologies.
    """
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoCommunityRepository()
    return SQLCommunityRepository(db)

def get_social_repository(db: AsyncSession = Depends(get_db)) -> SocialRepository:
    """
    Supplies explicit relational and identical payload routers scaling polymorphic discourse.
    """
    engine_type = os.getenv("DB_ENGINE", "SQL")
    if engine_type == "NOSQL":
        return MongoSocialRepository()
    return SQLSocialRepository(db)
