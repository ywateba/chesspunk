"""
Tests for SQL Match Repository
==============================
Tests all functions in core.repositories.sql.match_repo that interact with the SQL database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.sql.match_repo import SQLMatchRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.schemas import schemas
from core.db import models


@pytest.mark.asyncio
async def test_get_match(db_session: AsyncSession):
    """Test getting a match by ID."""
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    user_data1 = schemas.UserCreate(username="white", email="white@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="black", email="black@example.com", password="pass")
    white_player = await user_repo.create_user(user_data1, "hashed")
    black_player = await user_repo.create_user(user_data2, "hashed")

    # Create a match
    match = models.Match(
        competition_id=comp.id,
        white_player_id=white_player.id,
        black_player_id=black_player.id
    )
    created_matches = await match_repo.create_matches([match])
    created_match = created_matches[0]

    # Get the match
    fetched_match = await match_repo.get_match(created_match.id)

    assert fetched_match is not None
    assert fetched_match.id == created_match.id
    assert fetched_match.competition_id == comp.id
    assert fetched_match.white_player_id == white_player.id
    assert fetched_match.black_player_id == black_player.id


@pytest.mark.asyncio
async def test_get_match_not_found(db_session: AsyncSession):
    """Test getting a non-existent match."""
    repo = SQLMatchRepository(db_session)

    fetched_match = await repo.get_match(99999)
    assert fetched_match is None


@pytest.mark.asyncio
async def test_create_matches_single(db_session: AsyncSession):
    """Test creating a single match."""
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    user_data1 = schemas.UserCreate(username="white", email="white@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="black", email="black@example.com", password="pass")
    white_player = await user_repo.create_user(user_data1, "hashed")
    black_player = await user_repo.create_user(user_data2, "hashed")

    # Create a match
    match = models.Match(
        competition_id=comp.id,
        white_player_id=white_player.id,
        black_player_id=black_player.id
    )

    created_matches = await match_repo.create_matches([match])

    assert len(created_matches) == 1
    created_match = created_matches[0]
    assert created_match.id is not None
    assert created_match.competition_id == comp.id
    assert created_match.white_player_id == white_player.id
    assert created_match.black_player_id == black_player.id
    assert created_match.result == "*"  # default result


@pytest.mark.asyncio
async def test_create_matches_multiple(db_session: AsyncSession):
    """Test creating multiple matches at once."""
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    # Create 4 users for 2 matches
    users = []
    for i in range(4):
        user_data = schemas.UserCreate(
            username=f"player{i}",
            email=f"player{i}@example.com",
            password="pass"
        )
        user = await user_repo.create_user(user_data, "hashed")
        users.append(user)

    # Create 2 matches
    matches = [
        models.Match(competition_id=comp.id, white_player_id=users[0].id, black_player_id=users[1].id),
        models.Match(competition_id=comp.id, white_player_id=users[2].id, black_player_id=users[3].id),
    ]

    created_matches = await match_repo.create_matches(matches)

    assert len(created_matches) == 2
    for match in created_matches:
        assert match.id is not None
        assert match.competition_id == comp.id
        assert match.result == "*"


@pytest.mark.asyncio
async def test_update_match_result_only(db_session: AsyncSession):
    """Test updating a match result without PGN."""
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    user_data1 = schemas.UserCreate(username="white", email="white@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="black", email="black@example.com", password="pass")
    white_player = await user_repo.create_user(user_data1, "hashed")
    black_player = await user_repo.create_user(user_data2, "hashed")

    # Create and update a match
    match = models.Match(
        competition_id=comp.id,
        white_player_id=white_player.id,
        black_player_id=black_player.id
    )
    created_matches = await match_repo.create_matches([match])
    created_match = created_matches[0]

    # Update result
    updated_match = await match_repo.update_match(created_match, "1-0")

    assert updated_match.id == created_match.id
    assert updated_match.result == "1-0"
    assert updated_match.pgn_blueprint is None


@pytest.mark.asyncio
async def test_update_match_with_pgn(db_session: AsyncSession):
    """Test updating a match result with PGN blueprint."""
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    user_data1 = schemas.UserCreate(username="white", email="white@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="black", email="black@example.com", password="pass")
    white_player = await user_repo.create_user(user_data1, "hashed")
    black_player = await user_repo.create_user(user_data2, "hashed")

    # Create and update a match
    match = models.Match(
        competition_id=comp.id,
        white_player_id=white_player.id,
        black_player_id=black_player.id
    )
    created_matches = await match_repo.create_matches([match])
    created_match = created_matches[0]

    # Update result with PGN
    pgn = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 1-0"
    updated_match = await match_repo.update_match(created_match, "1-0", pgn)

    assert updated_match.id == created_match.id
    assert updated_match.result == "1-0"
    assert updated_match.pgn_blueprint == pgn


@pytest.mark.asyncio
async def test_update_match_multiple_times(db_session: AsyncSession):
    """Test updating a match multiple times."""
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    user_data1 = schemas.UserCreate(username="white", email="white@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="black", email="black@example.com", password="pass")
    white_player = await user_repo.create_user(user_data1, "hashed")
    black_player = await user_repo.create_user(user_data2, "hashed")

    # Create a match
    match = models.Match(
        competition_id=comp.id,
        white_player_id=white_player.id,
        black_player_id=black_player.id
    )
    created_matches = await match_repo.create_matches([match])
    created_match = created_matches[0]

    # Update multiple times
    updated_match1 = await match_repo.update_match(created_match, "1-0", "pgn1")
    updated_match2 = await match_repo.update_match(updated_match1, "0-1", "pgn2")

    assert updated_match2.result == "0-1"
    assert updated_match2.pgn_blueprint == "pgn2"