from pydantic import BaseModel
from typing import List



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
