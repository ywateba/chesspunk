"""
Competition Service
===================
Calculates Round Robin standings, tournament executions, and complex matchmaking matrix derivations seamlessly
independent of any data technology explicitly.
"""

from fastapi import HTTPException
from core.db import models
from core.schemas import schemas
from core.repositories.base import CompetitionRepository, MatchRepository, UserRepository
from core.services.elo_service import calculate_elo

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
            "player": player, "points": 0.0, "buchholz": 0.0,
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
                
    # Second iteration dynamically assigning buchholz values naturally deriving from opponents total points
    for match in comp.matches:
        if match.result != models.MatchResult.PENDING:
            w_id, b_id = match.white_player_id, match.black_player_id
            if w_id in standings and b_id in standings:
                standings[w_id]["buchholz"] += standings[b_id]["points"]
                standings[b_id]["buchholz"] += standings[w_id]["points"]

    # Rank sorting natively prioritizing points specifically, followed by general buchholz and wins threshold
    return sorted(standings.values(), key=lambda x: (x["points"], x["buchholz"], x["wins"]), reverse=True)

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
        
    # Branch matrix generation seamlessly based upon the explicit Competition format variables natively
    if getattr(comp, "format", "round_robin") == "swiss":
        standings = await get_standings(comp_repo, competition_id)
        played_edges = set()
        color_history = {p.id: 0 for p in players}
        
        for m in comp.matches:
            played_edges.add(tuple(sorted((m.white_player_id, m.black_player_id))))
            color_history[m.white_player_id] += 1
            color_history[m.black_player_id] -= 1

        unpaired = [s["player"].id for s in standings]
        matches = []
        
        while len(unpaired) > 1:
            p1 = unpaired.pop(0)
            paired_with = None
            for i, p2 in enumerate(unpaired):
                if tuple(sorted((p1, p2))) not in played_edges:
                    paired_with = p2
                    unpaired.pop(i)
                    break
            
            if paired_with is None:
                # Fallback if strict Swiss constraints are inherently impossible logically
                paired_with = unpaired.pop(0)
                
            if color_history.get(p1, 0) > color_history.get(paired_with, 0):
                matches.append(models.Match(competition_id=competition_id, white_player_id=paired_with, black_player_id=p1, result="*"))
            else:
                matches.append(models.Match(competition_id=competition_id, white_player_id=p1, black_player_id=paired_with, result="*"))
    else:
        # Generates cross-coupled array matches algorithmically without repetition (Round Robin)
        matches = [
            models.Match(competition_id=competition_id, white_player_id=players[i].id, black_player_id=players[j].id, result="*")
            for i in range(len(players)) for j in range(i + 1, len(players))
        ]
    
    # Commits batch writes completely abstractly protecting connections identically
    await match_repo.create_matches(matches)
    await comp_repo.update_competition_status(comp, "active")
    
    return {"message": f"Generated {len(matches)} matches"}

async def finish_competition(comp_repo: CompetitionRepository, user_repo: UserRepository, competition_id: int):
    """
    Analyzes finalized competition sets computing specific Mathematical rankings updating globally tracked objects sequentially.
    """
    comp = await get_competition(comp_repo, competition_id)
    if comp.status == "finished":
        raise HTTPException(status_code=400, detail="Competition is already marked finished")

    users_map = {p.id: p for p in comp.players}
    
    # Analyze raw matrices dynamically mapping chronological outcomes securely natively.
    for match in comp.matches:
        if match.result != models.MatchResult.PENDING:
            w_id, b_id = match.white_player_id, match.black_player_id
            if w_id in users_map and b_id in users_map:
                res_mapping = {
                    models.MatchResult.WHITE_WINS: 1.0,
                    models.MatchResult.BLACK_WINS: 0.0,
                    models.MatchResult.DRAW: 0.5
                }
                
                # Perform arithmetic logic updating cached entities globally
                w_new, b_new = calculate_elo(users_map[w_id].elo, users_map[b_id].elo, res_mapping[match.result])
                users_map[w_id].elo, users_map[b_id].elo = w_new, b_new

    # Pass object states down efficiently flushing DB commits
    for base in users_map.values():
        await user_repo.update_user_elo(base.id, base.elo)
        
    await comp_repo.update_competition_status(comp, "finished")
    return {"message": "Competition finalized and global ratings explicitly synchronized."}

