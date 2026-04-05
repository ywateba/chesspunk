"""
Tests for MongoDB Competition Repository
========================================
Comprehensive test suite for MongoCompetitionRepository covering all operations.
"""

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
import mongomock

# Patch mongomock.Database to ignore `authorizedCollections` missing keyword argument requested by Beanie>1.20 automatically
_original_list_collection_names = mongomock.Database.list_collection_names
def _patched_list_collection_names(self, *args, **kwargs):
    kwargs.pop('authorizedCollections', None)
    kwargs.pop('nameOnly', None)
    return _original_list_collection_names(self, *args, **kwargs)
mongomock.Database.list_collection_names = _patched_list_collection_names

from core.schemas import schemas
from core.db.documents import UserDocument, CompetitionDocument, MatchDocument
from core.repositories.nosql.user_repo import MongoUserRepository
from core.repositories.nosql.competition_repo import MongoCompetitionRepository


@pytest_asyncio.fixture(autouse=True)
async def init_mock_mongodb():
    """Initialize mock MongoDB for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[UserDocument, CompetitionDocument, MatchDocument]
    )
    yield


@pytest.mark.asyncio
class TestMongoCompetitionRepository:
    """Test suite for MongoCompetitionRepository."""

    @pytest.fixture
    async def comp_repo(self):
        """Fixture providing a fresh competition repository instance."""
        return MongoCompetitionRepository()

    @pytest.fixture
    async def user_repo(self):
        """Fixture providing a fresh user repository instance."""
        return MongoUserRepository()

    @pytest.fixture
    async def sample_competition_data(self):
        """Fixture providing sample competition creation data."""
        return schemas.CompetitionCreate(
            name="Test Tournament",
            description="A test chess tournament"
        )

    async def test_create_competition(self, comp_repo, sample_competition_data):
        """Test competition creation with proper data persistence."""
        # Create competition
        competition = await comp_repo.create_competition(sample_competition_data)

        # Assertions
        assert competition is not None
        assert competition.id is not None
        assert competition.name == sample_competition_data.name
        assert competition.description == sample_competition_data.description
        assert competition.status == "open"  # Default status
        assert competition.players == []  # Empty player list initially
        assert competition.created_at is not None

    async def test_get_competition(self, comp_repo, sample_competition_data):
        """Test retrieving competition by ID with related data."""
        # Create competition
        created_comp = await comp_repo.create_competition(sample_competition_data)

        # Retrieve competition by ID
        retrieved_comp = await comp_repo.get_competition(created_comp.id)

        # Assertions
        assert retrieved_comp is not None
        assert retrieved_comp.id == created_comp.id
        assert retrieved_comp.name == sample_competition_data.name
        assert retrieved_comp.players == []  # No players yet

    async def test_get_competition_not_found(self, comp_repo):
        """Test retrieving non-existent competition returns None."""
        retrieved_comp = await comp_repo.get_competition(mongomock.ObjectId())
        assert retrieved_comp is None

    async def test_get_competitions_pagination(self, comp_repo):
        """Test retrieving competitions with pagination."""
        # Create multiple competitions
        comps_data = [
            schemas.CompetitionCreate(name=f"Tournament {i}", description=f"Desc {i}")
            for i in range(5)
        ]

        created_comps = []
        for comp_data in comps_data:
            comp = await comp_repo.create_competition(comp_data)
            created_comps.append(comp)

        # Test pagination
        all_comps = await comp_repo.get_competitions(skip=0, limit=10)
        assert len(all_comps) == 5

        # Test with limit
        limited_comps = await comp_repo.get_competitions(skip=0, limit=2)
        assert len(limited_comps) == 2

        # Test with skip
        skipped_comps = await comp_repo.get_competitions(skip=2, limit=10)
        assert len(skipped_comps) == 3

    async def test_get_competitions_empty_database(self, comp_repo):
        """Test retrieving competitions from empty database."""
        comps = await comp_repo.get_competitions()
        assert comps == []

    async def test_add_player_to_competition(self, comp_repo, user_repo, sample_competition_data):
        """Test adding players to a competition."""
        # Create competition and users
        comp = await comp_repo.create_competition(sample_competition_data)
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="player1", email="p1@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="player2", email="p2@test.com", password="pass"),
            "hash2"
        )

        # Add first player
        updated_comp = await comp_repo.add_player_to_competition(comp, user1)
        assert any(str(player.id) == str(user1.id) for player in updated_comp.players)
        assert len(updated_comp.players) == 1

        # Add second player
        updated_comp = await comp_repo.add_player_to_competition(updated_comp, user2)
        assert any(str(player.id) == str(user2.id) for player in updated_comp.players)
        assert len(updated_comp.players) == 2

        # Verify through get_competition
        retrieved_comp = await comp_repo.get_competition(comp.id)
        assert len(retrieved_comp.players) == 2
        assert any(str(player.id) == str(user1.id) for player in retrieved_comp.players)
        assert any(str(player.id) == str(user2.id) for player in retrieved_comp.players)

    async def test_add_duplicate_player_to_competition(self, comp_repo, user_repo, sample_competition_data):
        """Test adding the same player multiple times doesn't create duplicates."""
        # Create competition and user
        comp = await comp_repo.create_competition(sample_competition_data)
        user = await user_repo.create_user(
            schemas.UserCreate(username="player", email="player@test.com", password="pass"),
            "hash"
        )

        # Add player first time
        updated_comp = await comp_repo.add_player_to_competition(comp, user)
        assert len(updated_comp.players) == 1

        # Add same player again
        updated_comp = await comp_repo.add_player_to_competition(updated_comp, user)
        assert len(updated_comp.players) == 1  # Should still be 1

    async def test_update_competition_status(self, comp_repo, sample_competition_data):
        """Test updating competition status."""
        # Create competition
        comp = await comp_repo.create_competition(sample_competition_data)
        assert comp.status == "open"

        # Update status to active
        updated_comp = await comp_repo.update_competition_status(comp, "active")
        assert updated_comp.status == "active"

        # Update status to finished
        updated_comp = await comp_repo.update_competition_status(updated_comp, "finished")
        assert updated_comp.status == "finished"

        # Verify through get_competition
        retrieved_comp = await comp_repo.get_competition(comp.id)
        assert retrieved_comp.status == "finished"

    async def test_competition_with_players_and_matches(self, comp_repo, user_repo, sample_competition_data):
        """Test competition retrieval with populated players and matches."""
        from core.repositories.nosql.match_repo import MongoMatchRepository
        match_repo = MongoMatchRepository()

        # Create competition and users
        comp = await comp_repo.create_competition(sample_competition_data)
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="player1", email="p1@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="player2", email="p2@test.com", password="pass"),
            "hash2"
        )

        # Add players
        comp = await comp_repo.add_player_to_competition(comp, user1)
        comp = await comp_repo.add_player_to_competition(comp, user2)

        # Create a match
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        matches = await match_repo.create_matches([payload])

        # Retrieve competition with all related data
        retrieved_comp = await comp_repo.get_competition(comp.id)

        # Assertions
        assert retrieved_comp is not None
        assert len(retrieved_comp.players) == 2
        assert len(retrieved_comp.matches) == 1
        assert str(retrieved_comp.matches[0].id) == str(matches[0].id)

    async def test_competition_data_integrity(self, comp_repo):
        """Test that competition data is stored and retrieved correctly."""
        comp_data = schemas.CompetitionCreate(
            name="Complex Tournament Name",
            description="A very detailed description with special characters: !@#$%^&*()"
        )

        # Create competition
        created_comp = await comp_repo.create_competition(comp_data)

        # Retrieve and verify
        retrieved_comp = await comp_repo.get_competition(created_comp.id)

        assert retrieved_comp.name == comp_data.name
        assert retrieved_comp.description == comp_data.description
        assert retrieved_comp.status == "open"

    async def test_multiple_competitions_isolation(self, comp_repo, user_repo):
        """Test that multiple competitions maintain data isolation."""
        # Create two competitions
        comp1_data = schemas.CompetitionCreate(name="Tournament 1", description="First tournament")
        comp2_data = schemas.CompetitionCreate(name="Tournament 2", description="Second tournament")

        comp1 = await comp_repo.create_competition(comp1_data)
        comp2 = await comp_repo.create_competition(comp2_data)

        # Create users
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="user1", email="u1@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="user2", email="u2@test.com", password="pass"),
            "hash2"
        )

        # Add different players to each competition
        comp1 = await comp_repo.add_player_to_competition(comp1, user1)
        comp2 = await comp_repo.add_player_to_competition(comp2, user2)

        # Verify isolation
        retrieved_comp1 = await comp_repo.get_competition(comp1.id)
        retrieved_comp2 = await comp_repo.get_competition(comp2.id)

        assert any(str(player.id) == str(user1.id) for player in retrieved_comp1.players)
        assert all(str(player.id) != str(user2.id) for player in retrieved_comp1.players)
        assert any(str(player.id) == str(user2.id) for player in retrieved_comp2.players)
        assert all(str(player.id) != str(user1.id) for player in retrieved_comp2.players)