"""
Beanie MongoDB Documents
========================
Defines the NoSQL abstractions mirroring SQLAlchemy models natively.
Uses built-in Pydantic constraints inheriting globally.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from beanie import Document, Link
from typing import Optional, List

class CommunityMember(BaseModel):
    user_id: str
    role: str = "member"
    rank: int = 0

class UserDocument(Document):
    email: str
    username: str
    hashed_password: str
    role: str = "player"
    elo: int = 1200
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

class MatchDocument(Document):
    competition_id: str
    white_player_id: str
    black_player_id: str
    result: str = "*"
    pgn_blueprint: Optional[str] = None
    
    class Settings:
        name = "matches"

class CompetitionDocument(Document):
    name: str
    format: str = "round_robin"
    status: str = "open"
    community_id: Optional[str] = None
    players: List[Link[UserDocument]] = []
    matches: List[Link[MatchDocument]] = []
    
    class Settings:
        name = "competitions"

class CommunityDocument(Document):
    name: str
    description: Optional[str] = None
    owner_id: str
    members: List[CommunityMember] = []
    
    class Settings:
        name = "communities"

class PostDocument(Document):
    community_id: str
    author_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "posts"

class CommentDocument(Document):
    entity_type: str # "post" or "match"
    entity_id: str
    author_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "comments"
        
    model_config = {"extra": "allow"}
