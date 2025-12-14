from pydantic import BaseModel
from typing import Optional


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
