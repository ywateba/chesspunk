from abc import ABC, abstractmethod
from typing import List, Optional, Any
from core.schemas import schemas
from core.db import models

class UserRepository(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[models.User]: pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[models.User]: pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[models.User]: pass
    
    @abstractmethod
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[models.User]: pass
    
    @abstractmethod
    async def create_user(self, user: schemas.UserCreate, hashed_password: str) -> models.User: pass


class CompetitionRepository(ABC):
    @abstractmethod
    async def get_competition(self, competition_id: int) -> Optional[models.Competition]: pass
    
    @abstractmethod
    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[models.Competition]: pass
    
    @abstractmethod
    async def create_competition(self, comp: schemas.CompetitionCreate) -> models.Competition: pass
    
    @abstractmethod
    async def add_player_to_competition(self, db_comp: Any, user: Any) -> models.Competition: pass
    
    @abstractmethod
    async def update_competition_status(self, db_comp: Any, status: str) -> models.Competition: pass


class MatchRepository(ABC):
    @abstractmethod
    async def get_match(self, match_id: int) -> Optional[models.Match]: pass
    
    @abstractmethod
    async def create_matches(self, matches: List[Any]) -> List[models.Match]: pass
    
    @abstractmethod
    async def update_match(self, db_match: Any, result: str, pgn_blueprint: str = None) -> models.Match: pass
