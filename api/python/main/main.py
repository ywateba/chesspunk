from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import engine, get_db

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chess Community API")

# --- Player Endpoints ---

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# --- Competition Endpoints ---

@app.post("/competitions/", response_model=schemas.Competition)
def create_competition(comp: schemas.CompetitionCreate, db: Session = Depends(get_db)):
    db_comp = models.Competition(name=comp.name)
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@app.post("/competitions/{competition_id}/join", response_model=schemas.Competition)
def join_competition(competition_id: int, user_id: int, db: Session = Depends(get_db)):
    # Get competition and user
    db_comp = db.query(models.Competition).filter(models.Competition.id == competition_id).first()
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not db_comp or not db_user:
        raise HTTPException(status_code=404, detail="Competition or User not found")
    
    # Add user to competition (Many-to-Many magic)
    db_comp.players.append(db_user)
    db.commit()
    db.refresh(db_comp)
    return db_comp

# --- Match Generation (Simple Round Robin POC) ---

@app.post("/competitions/{competition_id}/generate-matches")
def generate_matches(competition_id: int, db: Session = Depends(get_db)):
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
