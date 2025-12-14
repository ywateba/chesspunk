from pydantic import BaseModel
from typing import List
from core.schemas.user_schema import User
from core.schemas.match_schema import Match




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
