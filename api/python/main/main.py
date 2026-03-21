from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

import models, schemas
from database import engine, get_db

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chess Community API")

# --- Auth Utilities ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Player Endpoints ---

@app.post("/auth/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter((models.User.email == user.email) | (models.User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")
        
    db_user = models.User(username=user.username, email=user.email, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses 'username' field, we allow both username or email here
    user = db.query(models.User).filter((models.User.email == form_data.username) | (models.User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# --- Competition Endpoints ---

@app.post("/competitions/", response_model=schemas.Competition)
def create_competition(comp: schemas.CompetitionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_comp = models.Competition(name=comp.name)
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@app.post("/competitions/{competition_id}/join", response_model=schemas.Competition)
def join_competition(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Get competition
    db_comp = db.query(models.Competition).filter(models.Competition.id == competition_id).first()
    
    if not db_comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Add the authenticated user to the competition if not already joined
    if current_user not in db_comp.players:
        db_comp.players.append(current_user)
        db.commit()
        db.refresh(db_comp)
    return db_comp

# --- Match Generation (Simple Round Robin POC) ---

@app.post("/competitions/{competition_id}/generate-matches")
def generate_matches(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    SIMPLE POC LOGIC:
    Generates a Round Robin (everyone plays everyone once)
    """
    db_comp = db.query(models.Competition).filter(models.Competition.id == competition_id).first()
    players = db_comp.players
    
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="Not enough players to generate matches")

    matches_created = []
    
    # Simple loop to pair everyone with everyone
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            new_match = models.Match(
                competition_id=competition_id,
                white_player_id=players[i].id,
                black_player_id=players[j].id,
                result="*"
            )
            db.add(new_match)
            matches_created.append(new_match)
    
    db_comp.status = "active"
    db.commit()
    return {"message": f"Generated {len(matches_created)} matches"}

# --- Match Results ---

@app.put("/matches/{match_id}", response_model=schemas.Match)
def update_match_result(match_id: int, match_data: schemas.MatchUpdate, db: Session = Depends(get_db)):
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    db_match.result = match_data.result
    if match_data.pgn_blueprint:
        db_match.pgn_blueprint = match_data.pgn_blueprint
        
    db.commit()
    db.refresh(db_match)
    return db_match
