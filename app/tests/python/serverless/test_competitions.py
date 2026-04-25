import os
from unittest.mock import patch
from serverless.dynamodb import initialize_tables
from serverless.handlers import competitions, matches

@patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1"})
def test_competition_fide_lifecycle(aws_credentials, dynamodb_mock):
    initialize_tables()

    # 1. Create Competition
    comp = competitions.create_competition({"name": "FIDE Qualifier"})
    comp_id = comp["id"]
    
    # 2. Add 3 Players
    for p in ["p1", "p2", "p3"]:
        competitions.add_player(comp_id, {"player_id": p})
        
    # 3. Generate Matches (Round Robin)
    res = competitions.generate_matches(comp_id)
    generated_matches = res["matches"]
    assert len(generated_matches) == 3 # 3 players RR = 3 matches
    
    # Simulate match 1 (p1 vs p2) -> p1 wins
    m1 = generated_matches[0]
    matches.update_match_result(m1["id"], {"result": "WHITE_WINS"})
    
    # Simulate match 2 (p1 vs p3) -> Draw
    m2 = generated_matches[1]
    matches.update_match_result(m2["id"], {"result": "DRAW"})
    
    # 4. Standings Check
    standings = competitions.get_standings(comp_id)
    
    # p1 should have 1.5 points (1 win, 1 draw)
    p1_standing = next(s for s in standings if s["player_id"] == "p1")
    assert p1_standing["points"] == 1.5
    
    # 5. Finish Competition
    res = competitions.finish_competition(comp_id)
    assert "Competition finalized" in res["message"]
