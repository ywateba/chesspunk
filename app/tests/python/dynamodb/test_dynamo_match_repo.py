import pytest
from core.schemas import schemas
from core.repositories.dynamodb.match_repo import DynamoMatchRepository

@pytest.mark.asyncio
async def test_dynamo_match_repo_full_coverage():
    repo = DynamoMatchRepository()
    
    match_schema = schemas.MatchBase(white_player_id=1, black_player_id=2, result="*")
    setattr(match_schema, 'competition_id', 10)
    
    # 1. create_matches
    matches = await repo.create_matches([match_schema])
    assert len(matches) == 1
    assert getattr(matches[0], 'result') == "*"
    
    match_id = getattr(matches[0], 'id')
    
    # 2. get_match
    fetched = await repo.get_match(str(match_id))
    assert fetched is not None
    assert getattr(fetched, 'result') == "*"

    # 3. update_match (result only)
    updated = await repo.update_match(fetched, "1-0")
    assert getattr(updated, 'result') == "1-0"

    # 4. update_match (with pgn blueprint)
    updated_pgn = await repo.update_match(fetched, "1/2", "1. e4 e5")
    assert getattr(updated_pgn, 'result') == "1/2"
    assert getattr(updated_pgn, 'pgn_blueprint') == "1. e4 e5"
    
    # Invalid get
    assert await repo.get_match("invalid") is None
