from pydantic import BaseModel
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
    id: int
    class ConfigDict:
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
    model_config = {
        "json_schema_extra": {
            "example": {
                "result": "1-0",
                "pgn_blueprint": "1. e4 e5 2. Nf3"
            }
        }
    }

class Match(MatchBase):
    id: int
    competition_id: int
    pgn_blueprint: Optional[str] = None
    class ConfigDict:
        from_attributes = True

# --- Competition Schemas ---
class CompetitionBase(BaseModel):
    name: str
    format: str = "round_robin"

class CompetitionCreate(CompetitionBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Winter Regional Championship"
            }
        }
    }

class Competition(CompetitionBase):
    id: int
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
