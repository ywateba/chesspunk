import pytest
from core.schemas import schemas
from core.repositories.dynamodb.user_repo import DynamoUserRepository
from core.repositories.dynamodb.competition_repo import DynamoCompetitionRepository

@pytest.mark.asyncio
async def test_dynamo_competition_repo_full_coverage():
    comp_repo = DynamoCompetitionRepository()
    user_repo = DynamoUserRepository()
    
    # 1. create_competition
    schema = schemas.CompetitionCreate(name="Mega Tournament", format="round_robin")
    comp = await comp_repo.create_competition(schema)
    assert comp is not None
    assert getattr(comp, 'name') == "Mega Tournament"
    assert getattr(comp, 'status') == "open"
    assert getattr(comp, 'players', []) == []

    # 2. get_competition
    fetched = await comp_repo.get_competition(str(comp.id))
    assert fetched is not None
    assert str(fetched.id) == str(comp.id)

    # 3. update_competition_status
    updated = await comp_repo.update_competition_status(comp, "active")
    assert getattr(updated, 'status') == "active"

    # 4. get_competitions
    comps = await comp_repo.get_competitions()
    assert len(comps) >= 1
    assert any(str(c.id) == str(comp.id) for c in comps)

    # 5. add_player_to_competition
    user_schema = schemas.UserCreate(username="p1", email="p1@email.com", password="", role="", elo=0)
    user = await user_repo.create_user(user_schema, "")
    
    comp_with_player = await comp_repo.add_player_to_competition(comp, user)
    assert len(getattr(comp_with_player, 'players')) == 1
    assert str(comp_with_player.players[0].id) == str(user.id)
    
    # Duplicate add
    comp_with_player = await comp_repo.add_player_to_competition(comp_with_player, user)
    assert len(getattr(comp_with_player, 'players')) == 1
    
    # Invalid ID
    assert await comp_repo.get_competition("invalid") is None
