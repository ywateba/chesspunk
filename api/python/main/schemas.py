from pydantic import BaseModel
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

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
        orm_mode = True

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
        orm_mode = True
