"""
Beanie MongoDB Documents
========================
Defines the NoSQL abstractions mirroring SQLAlchemy models natively.
Uses built-in Pydantic constraints inheriting globally.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from beanie import Document, Link, PydanticObjectId
from typing import Optional, List, Any

class BaseDocument(Document):
    id: PydanticObjectId | str | None = Field(default=None, alias="_id")

    @field_validator("id", mode="before")
    def convert_id(cls, value):
        if value is None or isinstance(value, str):
            return value
        return str(value)

    model_config = {
        "json_encoders": {
            PydanticObjectId: str
        }
    }

class CommunityMember(BaseModel):
    user_id: str
    role: str = "member"
    rank: int = 0

class UserDocument(BaseDocument):
    email: str
    username: str
    hashed_password: str
    role: str = "player"
    elo: int = 1200
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

class MatchDocument(BaseDocument):
    competition_id: str
    white_player_id: str
    black_player_id: str
    result: str = "*"
    pgn_blueprint: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "matches"

class CompetitionDocument(BaseDocument):
    name: str
    format: str = "round_robin"
    status: str = "open"
    community_id: Optional[str] = None
    players: List[str] = []
    matches: List[Any] = []
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "competitions"

class CommunityDocument(BaseDocument):
    name: str
    description: Optional[str] = None
    owner_id: str
    members: List[CommunityMember] = []
    is_private: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "communities"

class PostDocument(BaseDocument):
    community_id: str
    author_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "posts"

class CommentDocument(BaseDocument):
    entity_type: str # "post" or "match"
    entity_id: str
    author_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "comments"
        
    model_config = {"extra": "allow"}
