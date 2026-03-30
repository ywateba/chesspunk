"""
Beanie MongoDB Documents
========================
Defines the NoSQL abstractions mirroring SQLAlchemy models natively.
Uses built-in Pydantic constraints inheriting globally.
"""

from beanie import Document
from pydantic import Field
from typing import List, Optional
from datetime import datetime

class UserDocument(Document):
    email: str
    username: str
    hashed_password: str
    role: str = "player"
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
    status: str = "planned"
    format: str = "round_robin"
    player_ids: List[str] = []
    
    class Settings:
        name = "competitions"
        
    model_config = {"extra": "allow"}
