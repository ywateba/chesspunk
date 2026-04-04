"""
Repository Base Contracts
=========================
Defines the strict Abstract Base Classes (ABCs) that ensure identical schemas
between entirely distinct physical database methodologies (PostgreSQL vs MongoDB).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from core.schemas import schemas

class UserRepository(ABC):
    """
    Defines structural limits over native Account retrieval mechanics universally.
    """
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Any]: pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Any]: pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[Any]: pass

    @abstractmethod
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[Any]: pass

    @abstractmethod
    async def create_user(self, user: schemas.UserCreate, hashed_password: str) -> Any: pass

    @abstractmethod
    async def update_user_elo(self, user_id: str, new_elo: int) -> Optional[Any]: pass

class CompetitionRepository(ABC):
    """
    Evaluates strictly bound tournament executions requiring precise mapping
    constraints across native connections explicitly.
    """
    @abstractmethod
    async def get_competition(self, competition_id: str) -> Optional[Any]: pass

    @abstractmethod
    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[Any]: pass

    @abstractmethod
    async def create_competition(self, comp: schemas.CompetitionCreate) -> Any: pass

    @abstractmethod
    async def add_player_to_competition(self, db_comp: Any, user: Any) -> Any: pass

    @abstractmethod
    async def update_competition_status(self, db_comp: Any, status: str) -> Any: pass

class MatchRepository(ABC):
    """
    Abstract bounds verifying strict Match execution and PGN manipulation behaviors explicitly.
    """
    @abstractmethod
    async def get_match(self, match_id: str) -> Optional[Any]: pass

    @abstractmethod
    async def create_matches(self, matches: List[Any]) -> List[Any]: pass

    @abstractmethod
    async def update_match(self, db_match: Any, result: str, pgn_blueprint: str = None) -> Any: pass

class CommunityRepository(ABC):
    """
    Contracts defining exact multi-tenant social clubs natively avoiding implementation specifics.
    """
    @abstractmethod
    async def create_community(self, comm: schemas.CommunityCreate, owner_id: str) -> Any: pass
    
    @abstractmethod
    async def get_community(self, community_id: str) -> Optional[Any]: pass
    
    @abstractmethod
    async def get_communities(self, skip: int = 0, limit: int = 100) -> List[Any]: pass
    
    @abstractmethod
    async def join_community(self, community_id: str, user_id: str, role: str = "member") -> Any: pass
    
    @abstractmethod
    async def get_members(self, community_id: str) -> List[Any]: pass

class SocialRepository(ABC):
    """
    Contracts defining exact polymorphic comment and nested post distributions smoothly.
    """
    @abstractmethod
    async def create_post(self, community_id: str, author_id: str, content: str) -> Any: pass
    
    @abstractmethod
    async def get_posts(self, community_id: str, skip: int = 0, limit: int = 50) -> List[Any]: pass
    
    @abstractmethod
    async def create_comment(self, entity_type: str, entity_id: str, author_id: str, content: str) -> Any: pass
    
    @abstractmethod
    async def get_comments(self, entity_type: str, entity_id: str, skip: int = 0, limit: int = 50) -> List[Any]: pass
