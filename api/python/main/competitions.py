from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from auth_utils import get_current_user

router = APIRouter(prefix="/competitions", tags=["competitions"])

@router.post("/", response_model=schemas.Competition)
def create_competition(comp: schemas.CompetitionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_comp = models.Competition(name=comp.name)
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.post("/{competition_id}/join", response_model=schemas.Competition)
def join_competition(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_comp = db.query(models.Competition).filter(models.Competition.id == competition_id).first()
    
    if not db_comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if current_user not in db_comp.players:
        db_comp.players.append(current_user)
        db.commit()
        db.refresh(db_comp)
    return db_comp

@router.get("/{competition_id}/standings", response_model=List[schemas.PlayerStanding])
def get_standings(competition_id: int, db: Session = Depends(get_db)):
    db_comp = db.query(models.Competition).filter(models.Competition.id == competition_id).first()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Competition not found")
        
    standings = {}
    for player in db_comp.players:
        standings[player.id] = {
            "player": player,
            "points": 0.0,
            "matches_played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0
        }
        
    for match in db_comp.matches:
        if match.result == models.MatchResult.PENDING:
            continue
            
        w_id, b_id = match.white_player_id, match.black_player_id
        
        if w_id in standings and b_id in standings:
            standings[w_id]["matches_played"] += 1
            standings[b_id]["matches_played"] += 1
            
            if match.result == models.MatchResult.WHITE_WINS:
                standings[w_id]["wins"] += 1; standings[w_id]["points"] += 1.0
                standings[b_id]["losses"] += 1
            elif match.result == models.MatchResult.BLACK_WINS:
                standings[b_id]["wins"] += 1; standings[b_id]["points"] += 1.0
                standings[w_id]["losses"] += 1
            elif match.result == models.MatchResult.DRAW:
                standings[w_id]["draws"] += 1; standings[w_id]["points"] += 0.5
                standings[b_id]["draws"] += 1; standings[b_id]["points"] += 0.5
                
    return sorted(standings.values(), key=lambda x: (x["points"], x["wins"]), reverse=True)

@router.post("/{competition_id}/generate-matches")
def generate_matches(competition_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_comp = db.query(models.Competition).filter(models.Competition.id == competition_id).first()
    players = db_comp.players
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="Not enough players to generate matches")
    matches_created = [models.Match(competition_id=competition_id, white_player_id=players[i].id, black_player_id=players[j].id, result="*") for i in range(len(players)) for j in range(i + 1, len(players))]
    db.add_all(matches_created)
    db_comp.status = "active"
    db.commit()
    return {"message": f"Generated {len(matches_created)} matches"}