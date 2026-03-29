"""
Competition Service
===================
Calculates Round Robin standings, tournament executions, and complex matchmaking matrix derivations seamlessly
independent of any data technology explicitly.
"""

from fastapi import HTTPException
from core.db import models
from core.schemas import schemas
from core.repositories.base import CompetitionRepository, MatchRepository

async def get_competitions(comp_repo: CompetitionRepository, skip: int = 0, limit: int = 100):
    """
    Return mapped generic tournaments globally isolated.
    """
    return await comp_repo.get_competitions(skip=skip, limit=limit)

async def get_competition(comp_repo: CompetitionRepository, competition_id: int):
    """
    Retrieve specific tournament structures safely tracking 404 constraints dynamically.
    """
    comp = await comp_repo.get_competition(competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return comp

async def create_competition(comp_repo: CompetitionRepository, comp: schemas.CompetitionCreate):
    """
    Launch native empty tournament constructs persisting globally.
    """
    return await comp_repo.create_competition(comp)

async def join_competition(comp_repo: CompetitionRepository, competition_id: int, current_user: models.User):
    """
    Appends explicitly verified player connections natively allocating users
    as recognized contenders to designated competition rosters.
    """
    comp = await get_competition(comp_repo, competition_id)
    return await comp_repo.add_player_to_competition(comp, current_user)

async def get_standings(comp_repo: CompetitionRepository, competition_id: int):
    """
    Calculates leaderboard mechanics directly parsing tournament match outcomes dynamically.
    Points are yielded exclusively natively per FIDE rules:
    - 1.0 points for a Win
    - 0.5 points for a Draw
    - 0.0 points for a Loss / Pending match
    """
    comp = await get_competition(comp_repo, competition_id)
    standings = {}
    
    # Pre-allocate empty tracking arrays mapped by FIDE configurations
    for player in comp.players:
        standings[player.id] = {
            "player": player, "points": 0.0,
            "matches_played": 0, "wins": 0, "draws": 0, "losses": 0
        }
        
    # Evaluate score aggregates isolated over match results structurally mapping rules
    for match in comp.matches:
        if match.result == models.MatchResult.PENDING:
            continue
            
        w_id, b_id = match.white_player_id, match.black_player_id
        if w_id in standings and b_id in standings:
            standings[w_id]["matches_played"] += 1
            standings[b_id]["matches_played"] += 1
            
            # Map Win/Draws/Loss logic dynamically ranking algorithms safely mapping execution models
            if match.result == models.MatchResult.WHITE_WINS:
                standings[w_id]["wins"] += 1; standings[w_id]["points"] += 1.0
                standings[b_id]["losses"] += 1
            elif match.result == models.MatchResult.BLACK_WINS:
                standings[b_id]["wins"] += 1; standings[b_id]["points"] += 1.0
                standings[w_id]["losses"] += 1
            elif match.result == models.MatchResult.DRAW:
                standings[w_id]["draws"] += 1; standings[w_id]["points"] += 0.5
                standings[b_id]["draws"] += 1; standings[b_id]["points"] += 0.5
                
    # Rank sorting natively prioritizing points specifically, followed by general win thresholds
    return sorted(standings.values(), key=lambda x: (x["points"], x["wins"]), reverse=True)

async def generate_matches(comp_repo: CompetitionRepository, match_repo: MatchRepository, competition_id: int):
    """
    Transforms pending empty competition constraints locking them fully active executing Round Robin structures explicitly.
    Matches every player dynamically internally calculating opposing grids seamlessly over iteration pipelines natively.
    """
    comp = await get_competition(comp_repo, competition_id)
    players = comp.players
    
    # Must hit dual player metrics before proceeding
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="Not enough players to generate matches")
        
    # Generates cross-coupled array matches algorithmically without repetition
    matches = [
        models.Match(competition_id=competition_id, white_player_id=players[i].id, black_player_id=players[j].id, result="*")
        for i in range(len(players)) for j in range(i + 1, len(players))
    ]
    
    # Commits batch writes completely abstractly protecting connections identically
    await match_repo.create_matches(matches)
    await comp_repo.update_competition_status(comp, "active")
    
    return {"message": f"Generated {len(matches)} matches"}
