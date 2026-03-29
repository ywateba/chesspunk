from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.schemas import schemas
from core.auth.utils import get_current_user
from core.db import models
from core.db.database import get_db
from core.services import user_service


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return user_service.get_users_list(db, skip=skip, limit=limit)