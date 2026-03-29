from sqlalchemy.orm import Session
from core.db.crud import users as users_crud
from core.schemas import schemas
from core.auth.utils import verify_password, get_password_hash
from core.db import models
from typing import Optional

def get_user_by_email_or_username(db: Session, identifier: str) -> Optional[models.User]:
    user = users_crud.get_user_by_email(db, identifier)
    if not user:
        user = users_crud.get_user_by_username(db, identifier)
    return user

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    return users_crud.create_user(db, user, hashed_password)

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_email_or_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
