"""
Authentication Router
=====================
Handles user signup, login, and bearer token generation.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from core.schemas import schemas
from core.auth.utils import create_access_token
from core.services.auth_service import get_user_by_email_or_username, create_user, authenticate_user
from core.dependencies import get_user_repository
from core.repositories.base import UserRepository
from core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=schemas.User)
async def signup(user: schemas.UserCreate, user_repo: UserRepository = Depends(get_user_repository)):
    """
    Register a new user in the system.
    
    Validates uniqueness of both email and username against the database configuration
    yielded by the active repository.
    """
    # Check if user already exists by email
    existing_user = await get_user_by_email_or_username(user_repo, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if user already exists by username (if different from email)
    if user.username != user.email:
        existing_user = await get_user_by_email_or_username(user_repo, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
    
    # Delegate to auth service for proper password hashing and creation
    db_user = await create_user(user_repo, user)
    return db_user

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), user_repo: UserRepository = Depends(get_user_repository)):
    """
    Authenticate a user via username and password, returning a JWT access token.
    """
    # Authenticate credentials through the service layer safely
    user = await authenticate_user(user_repo, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
        
    # Generate temporary JWT session token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}