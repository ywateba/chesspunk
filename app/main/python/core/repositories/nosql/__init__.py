"""
NoSQL Repositories Package
==========================
Provides MongoDB implementations of all repository interfaces using Beanie ODM.
All repositories follow the same abstract contracts as SQL repositories for
consistent API across different database backends.
"""

from .user_repo import MongoUserRepository
from .competition_repo import MongoCompetitionRepository
from .match_repo import MongoMatchRepository
from .community_repo import MongoCommunityRepository
from .social_repo import MongoSocialRepository

__all__ = [
    "MongoUserRepository",
    "MongoCompetitionRepository",
    "MongoMatchRepository",
    "MongoCommunityRepository",
    "MongoSocialRepository"
]