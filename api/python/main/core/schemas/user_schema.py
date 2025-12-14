from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    is_player: bool = False

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        orm_mode = True
