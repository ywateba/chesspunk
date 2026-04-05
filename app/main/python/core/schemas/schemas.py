from datetime import datetime

from pydantic import BaseModel, Field
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str
    role: str = "player"
    elo: int = 1200

class UserCreate(UserBase):
    password: str
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "grandmaster",
                "email": "gm@chess.com",
                "role": "player",
                "elo": 1200,
                "password": "strongPassword123!"
            }
        }
    }

class User(UserBase):
    id: str
    class ConfigDict:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Match Schemas ---
class MatchBase(BaseModel):
    white_player_id: str
    black_player_id: str
    result: str = "*"

class MatchUpdate(BaseModel):
    result: str
    pgn_blueprint: Optional[str] = None
    model_config = {
        "json_schema_extra": {
            "example": {
                "result": "1-0",
                "pgn_blueprint": "1. e4 e5 2. Nf3"
            }
        }
    }

class Match(MatchBase):
    id: str
    competition_id: str
    pgn_blueprint: Optional[str] = None
    class ConfigDict:
        from_attributes = True

# --- Competition Schemas ---
class CompetitionBase(BaseModel):
    name: str
    format: str = "round_robin"
    community_id: Optional[str] = None
    description: Optional[str] = None

class CompetitionCreate(CompetitionBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Winter Regional Championship"
            }
        }
    }

class Competition(CompetitionBase):
    id: str
    status: str
    players: List[User] = []
    matches: List[Match] = []
    class ConfigDict:
        from_attributes = True

class PlayerStanding(BaseModel):
    player: User
    points: float = 0.0
    buchholz: float = 0.0
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    # We don't need orm_mode here because we will build these dictionaries dynamically

# --- Community Schemas ---
class CommunityBase(BaseModel):
    name: str
    description: Optional[str] = None

class CommunityCreate(CommunityBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_private: bool = False

class CommunityMemberSchema(BaseModel):
    user_id: str
    role: str
    rank: int
    class ConfigDict:
        from_attributes = True

class Community(CommunityBase):
    id: str
    owner_id: str
    members: List[CommunityMemberSchema] = []
    class ConfigDict:
        from_attributes = True

# --- Social Schemas ---
class PostBase(BaseModel):
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: str
    community_id: str
    author_id: str
    class ConfigDict:
        from_attributes = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: str
    entity_type: str
    entity_id: str
    author_id: str
    class ConfigDict:
        from_attributes = True
