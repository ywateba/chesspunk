from pydantic import BaseModel
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Match Schemas ---
class MatchBase(BaseModel):
    white_player_id: int
    black_player_id: int
    result: str = "*"

class MatchUpdate(BaseModel):
    result: str
    pgn_blueprint: Optional[str] = None

class Match(MatchBase):
    id: int
    competition_id: int
    pgn_blueprint: Optional[str] = None
    class Config:
        from_attributes = True

# --- Competition Schemas ---
class CompetitionBase(BaseModel):
    name: str

class CompetitionCreate(CompetitionBase):
    pass

class Competition(CompetitionBase):
    id: int
    status: str
    players: List[User] = []
    matches: List[Match] = []
    class Config:
        from_attributes = True

class PlayerStanding(BaseModel):
    player: User
    points: float = 0.0
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    # We don't need orm_mode here because we will build these dictionaries dynamically
