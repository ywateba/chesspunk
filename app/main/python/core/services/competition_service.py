from fastapi import HTTPException
from core.db import models
from core.schemas import schemas
from core.repositories.base import CompetitionRepository, MatchRepository

async def get_competitions(comp_repo: CompetitionRepository, skip: int = 0, limit: int = 100):
    return await comp_repo.get_competitions(skip=skip, limit=limit)

async def get_competition(comp_repo: CompetitionRepository, competition_id: int):
    comp = await comp_repo.get_competition(competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return comp

async def create_competition(comp_repo: CompetitionRepository, comp: schemas.CompetitionCreate):
    return await comp_repo.create_competition(comp)

async def join_competition(comp_repo: CompetitionRepository, competition_id: int, current_user: models.User):
    comp = await get_competition(comp_repo, competition_id)
    return await comp_repo.add_player_to_competition(comp, current_user)

async def get_standings(comp_repo: CompetitionRepository, competition_id: int):
    comp = await get_competition(comp_repo, competition_id)
    standings = {}
    for player in comp.players:
        standings[player.id] = {
            "player": player, "points": 0.0,
            "matches_played": 0, "wins": 0, "draws": 0, "losses": 0
        }
    for match in comp.matches:
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

async def generate_matches(comp_repo: CompetitionRepository, match_repo: MatchRepository, competition_id: int):
    comp = await get_competition(comp_repo, competition_id)
    players = comp.players
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="Not enough players to generate matches")
    matches = [
        models.Match(competition_id=competition_id, white_player_id=players[i].id, black_player_id=players[j].id, result="*")
        for i in range(len(players)) for j in range(i + 1, len(players))
    ]
    await match_repo.create_matches(matches)
    await comp_repo.update_competition_status(comp, "active")
    return {"message": f"Generated {len(matches)} matches"}
