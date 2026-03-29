from sqlalchemy.orm import Session
from core.db.crud import users as users_crud

def get_users_list(db: Session, skip: int = 0, limit: int = 100):
    return users_crud.get_users(db, skip=skip, limit=limit)
