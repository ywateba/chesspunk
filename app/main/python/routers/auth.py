from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from core.schemas import schemas
from core.auth.utils import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from core.services.auth_service import get_user_by_email_or_username, create_user, authenticate_user
from core.db.database import get_db


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists by email
    existing_user = get_user_by_email_or_username(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if user already exists by username (if different from email)
    if user.username != user.email:
        existing_user = get_user_by_email_or_username(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = create_user(db, user)
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}