"""
Tests for SQL Competition Repository
====================================
Tests all functions in core.repositories.sql.competition_repo that interact with the SQL database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.schemas import schemas
from core.db import models


@pytest.mark.asyncio
async def test_get_competition(db_session: AsyncSession):
    """Test getting a competition by ID."""
    repo = SQLCompetitionRepository(db_session)

    # Create a competition
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    created_comp = await repo.create_competition(comp_data)

    # Get the competition
    fetched_comp = await repo.get_competition(created_comp.id)

    assert fetched_comp is not None
    assert fetched_comp.id == created_comp.id
    assert fetched_comp.name == "Test Tournament"


@pytest.mark.asyncio
async def test_get_competition_not_found(db_session: AsyncSession):
    """Test getting a non-existent competition."""
    repo = SQLCompetitionRepository(db_session)

    fetched_comp = await repo.get_competition(99999)
    assert fetched_comp is None


@pytest.mark.asyncio
async def test_get_competitions(db_session: AsyncSession):
    """Test getting paginated list of competitions."""
    repo = SQLCompetitionRepository(db_session)

    # Create multiple competitions
    comps_data = [
        schemas.CompetitionCreate(name="Tournament 1"),
        schemas.CompetitionCreate(name="Tournament 2"),
        schemas.CompetitionCreate(name="Tournament 3"),
    ]

    for comp_data in comps_data:
        await repo.create_competition(comp_data)

    # Get all competitions
    competitions = await repo.get_competitions()
    assert len(competitions) >= 3

    # Check that our competitions are in the list
    names = [comp.name for comp in competitions]
    assert "Tournament 1" in names
    assert "Tournament 2" in names
    assert "Tournament 3" in names


@pytest.mark.asyncio
async def test_get_competitions_pagination(db_session: AsyncSession):
    """Test competitions pagination."""
    repo = SQLCompetitionRepository(db_session)

    # Create 5 competitions
    for i in range(5):
        comp_data = schemas.CompetitionCreate(name=f"Tournament {i}")
        await repo.create_competition(comp_data)

    # Get first 2 competitions
    competitions = await repo.get_competitions(skip=0, limit=2)
    assert len(competitions) == 2

    # Get next 2 competitions
    competitions = await repo.get_competitions(skip=2, limit=2)
    assert len(competitions) == 2


@pytest.mark.asyncio
async def test_create_competition(db_session: AsyncSession):
    """Test creating a new competition."""
    repo = SQLCompetitionRepository(db_session)

    comp_data = schemas.CompetitionCreate(name="New Tournament")
    created_comp = await repo.create_competition(comp_data)

    assert created_comp.id is not None
    assert created_comp.name == "New Tournament"
    #assert created_comp.status == "pending"  # default status


@pytest.mark.asyncio
async def test_add_player_to_competition(db_session: AsyncSession):
    """Test adding a player to a competition."""
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create competition and user
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    created_comp = await comp_repo.create_competition(comp_data)

    user_data = schemas.UserCreate(username="player", email="player@example.com", password="password")
    created_user = await user_repo.create_user(user_data, "hashed")

    # Add player to competition
    updated_comp = await comp_repo.add_player_to_competition(created_comp, created_user)

    assert len(updated_comp.players) == 1
    assert updated_comp.players[0].id == created_user.id


@pytest.mark.asyncio
async def test_add_player_to_competition_duplicate(db_session: AsyncSession):
    """Test adding the same player to a competition multiple times."""
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create competition and user
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    created_comp = await comp_repo.create_competition(comp_data)

    user_data = schemas.UserCreate(username="player", email="player@example.com", password="password")
    created_user = await user_repo.create_user(user_data, "hashed")

    # Add player to competition twice
    updated_comp1 = await comp_repo.add_player_to_competition(created_comp, created_user)
    updated_comp2 = await comp_repo.add_player_to_competition(updated_comp1, created_user)

    # Should still only have one player
    assert len(updated_comp2.players) == 1
    assert updated_comp2.players[0].id == created_user.id


@pytest.mark.asyncio
async def test_update_competition_status(db_session: AsyncSession):
    """Test updating a competition's status."""
    repo = SQLCompetitionRepository(db_session)

    # Create a competition
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    created_comp = await repo.create_competition(comp_data)

    # Update status
    updated_comp = await repo.update_competition_status(created_comp, "active")

    assert updated_comp.id == created_comp.id
    assert updated_comp.status == "active"


@pytest.mark.asyncio
async def test_competition_with_players_and_matches(db_session: AsyncSession):
    """Test getting a competition with its players and matches loaded."""
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create competition
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    created_comp = await comp_repo.create_competition(comp_data)

    # Create users and add them to competition
    user_data1 = schemas.UserCreate(username="player1", email="p1@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="player2", email="p2@example.com", password="pass")
    user1 = await user_repo.create_user(user_data1, "hashed")
    user2 = await user_repo.create_user(user_data2, "hashed")

    updated_comp = await comp_repo.add_player_to_competition(created_comp, user1)
    updated_comp = await comp_repo.add_player_to_competition(updated_comp, user2)

    # Fetch competition with relationships
    fetched_comp = await comp_repo.get_competition(updated_comp.id)

    assert fetched_comp is not None
    assert len(fetched_comp.players) == 2
    player_ids = [p.id for p in fetched_comp.players]
    assert user1.id in player_ids
    assert user2.id in player_ids
    assert len(fetched_comp.matches) == 0  # No matches yet