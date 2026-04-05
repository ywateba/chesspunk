"""
Tests for MongoDB Match Repository
==================================
Comprehensive test suite for MongoMatchRepository covering all operations.
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
from core.repositories.nosql.match_repo import MongoMatchRepository


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
class TestMongoMatchRepository:
    """Test suite for MongoMatchRepository."""

    @pytest.fixture
    async def match_repo(self):
        """Fixture providing a fresh match repository instance."""
        return MongoMatchRepository()

    @pytest.fixture
    async def user_repo(self):
        """Fixture providing a fresh user repository instance."""
        return MongoUserRepository()

    @pytest.fixture
    async def comp_repo(self):
        """Fixture providing a fresh competition repository instance."""
        return MongoCompetitionRepository()

    async def test_get_match(self, match_repo, user_repo, comp_repo):
        """Test retrieving match by ID."""
        # Setup: Create competition and users
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Test Match Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="white", email="white@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="black", email="black@test.com", password="pass"),
            "hash2"
        )

        # Create match payload
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        created_matches = await match_repo.create_matches([payload])
        created_match = created_matches[0]

        # Retrieve match by ID
        retrieved_match = await match_repo.get_match(created_match.id)

        # Assertions
        assert retrieved_match is not None
        assert retrieved_match.id == created_match.id
        assert retrieved_match.competition_id == str(comp.id)
        assert retrieved_match.white_player_id == str(user1.id)
        assert retrieved_match.black_player_id == str(user2.id)
        assert retrieved_match.result == "*"

    async def test_get_match_not_found(self, match_repo):
        """Test retrieving non-existent match returns None."""
        retrieved_match = await match_repo.get_match(99999)
        assert retrieved_match is None

    async def test_create_matches_single(self, match_repo, user_repo, comp_repo):
        """Test creating a single match."""
        # Setup
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Single Match Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="player1", email="p1@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="player2", email="p2@test.com", password="pass"),
            "hash2"
        )

        # Create match payload
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        created_matches = await match_repo.create_matches([payload])

        # Assertions
        assert len(created_matches) == 1
        match = created_matches[0]
        assert match.id is not None
        assert match.competition_id == str(comp.id)
        assert match.white_player_id == str(user1.id)
        assert match.black_player_id == str(user2.id)
        assert match.result == "*"
        assert match.pgn_blueprint is None
        assert match.created_at is not None

    async def test_create_matches_multiple(self, match_repo, user_repo, comp_repo):
        """Test creating multiple matches at once."""
        # Setup
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Multi Match Comp"))
        users = []
        for i in range(4):
            user = await user_repo.create_user(
                schemas.UserCreate(username=f"player{i}", email=f"p{i}@test.com", password="pass"),
                f"hash{i}"
            )
            users.append(user)

        # Create multiple match payloads
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payloads = [
            FakeMatchPayload(comp.id, users[0].id, users[1].id, "*"),
            FakeMatchPayload(comp.id, users[2].id, users[3].id, "*"),
        ]
        created_matches = await match_repo.create_matches(payloads)

        # Assertions
        assert len(created_matches) == 2
        for i, match in enumerate(created_matches):
            assert match.id is not None
            assert match.competition_id == str(comp.id)
            assert match.result == "*"
            assert match.pgn_blueprint is None

        # Verify matches are different
        assert created_matches[0].id != created_matches[1].id

    async def test_create_matches_empty_list(self, match_repo):
        """Test creating matches with empty list."""
        created_matches = await match_repo.create_matches([])
        assert created_matches == []

    async def test_update_match_result_only(self, match_repo, user_repo, comp_repo):
        """Test updating match result without PGN."""
        # Setup
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Update Match Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="white", email="white@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="black", email="black@test.com", password="pass"),
            "hash2"
        )

        # Create match
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        created_matches = await match_repo.create_matches([payload])
        match = created_matches[0]

        # Update result
        updated_match = await match_repo.update_match(match, "1-0")

        # Assertions
        assert updated_match is not None
        assert updated_match.id == match.id
        assert updated_match.result == "1-0"
        assert updated_match.pgn_blueprint is None

    async def test_update_match_with_pgn(self, match_repo, user_repo, comp_repo):
        """Test updating match result with PGN blueprint."""
        # Setup
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="PGN Match Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="white", email="white@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="black", email="black@test.com", password="pass"),
            "hash2"
        )

        # Create match
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        created_matches = await match_repo.create_matches([payload])
        match = created_matches[0]

        # Update with PGN
        pgn_data = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6"
        updated_match = await match_repo.update_match(match, "1-0", pgn_data)

        # Assertions
        assert updated_match is not None
        assert updated_match.id == match.id
        assert updated_match.result == "1-0"
        assert updated_match.pgn_blueprint == pgn_data

    async def test_update_match_multiple_times(self, match_repo, user_repo, comp_repo):
        """Test updating the same match multiple times."""
        # Setup
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Multi Update Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="white", email="white@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="black", email="black@test.com", password="pass"),
            "hash2"
        )

        # Create match
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        created_matches = await match_repo.create_matches([payload])
        match = created_matches[0]

        # First update
        updated_match = await match_repo.update_match(match, "1-0", "1. e4")
        assert updated_match.result == "1-0"
        assert updated_match.pgn_blueprint == "1. e4"

        # Second update (only result)
        updated_match = await match_repo.update_match(updated_match, "0-1")
        assert updated_match.result == "0-1"
        assert updated_match.pgn_blueprint == "1. e4"  # Should remain unchanged

        # Third update (result and PGN)
        updated_match = await match_repo.update_match(updated_match, "1/2-1/2", "1. e4 e5 2. Nf3 Nc6 1/2-1/2")
        assert updated_match.result == "1/2-1/2"
        assert updated_match.pgn_blueprint == "1. e4 e5 2. Nf3 Nc6 1/2-1/2"

    async def test_update_match_not_found(self, match_repo):
        """Test updating non-existent match."""
        # Create a fake match object
        class FakeMatch:
            def __init__(self):
                self.id = "fake_id"
                self.result = "*"
                self.pgn_blueprint = None

        fake_match = FakeMatch()
        # This should not raise an exception but the match won't be found
        # In practice, this would be handled by the service layer
        updated_match = await match_repo.update_match(fake_match, "1-0")
        assert updated_match == fake_match

    async def test_match_data_integrity(self, match_repo, user_repo, comp_repo):
        """Test that match data is stored and retrieved correctly."""
        # Setup
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Data Integrity Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="white", email="white@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="black", email="black@test.com", password="pass"),
            "hash2"
        )

        # Create match with complex data
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        created_matches = await match_repo.create_matches([payload])
        created_match = created_matches[0]

        # Update with complex PGN
        complex_pgn = """[Event "Test Match"]
[Site "Test Site"]
[Date "2024.12.01"]
[Round "1"]
[White "White Player"]
[Black "Black Player"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6
8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 11. c4 c6 12. cxb5 axb5 13. Nc3 Bb7
14. Bg5 b4 15. Nb1 h6 16. Bh4 c5 17. dxe5 dxe5 18. Qxd8 Raxd8 19. Nxe5 Nxe5
20. Rxe5 Bc6 21. Bxf6 Bxf6 22. Rxf6 gxf6 23. Bxf7+ Kh7 24. Bxd5 Bxd5
25. exd5 Rd6 26. Rc1 Rc8 27. Rc5 Rxc5 28. bxc5 Rc6 29. c6 Kg6 30. g4 h5
31. gxh5+ Kxh5 32. Kg2 Kg4 33. h4 Kf4 34. h5 Ke4 35. h6 Kd4 36. h7 Rc8
37. c7 Kd5 38. h8=Q Rxh8 39. c8=Q 1-0"""

        updated_match = await match_repo.update_match(created_match, "1-0", complex_pgn)

        # Retrieve and verify
        retrieved_match = await match_repo.get_match(created_match.id)

        assert retrieved_match.result == "1-0"
        assert retrieved_match.pgn_blueprint == complex_pgn
        assert retrieved_match.competition_id == str(comp.id)
        assert retrieved_match.white_player_id == str(user1.id)
        assert retrieved_match.black_player_id == str(user2.id)

    async def test_matches_isolation(self, match_repo, user_repo, comp_repo):
        """Test that matches from different competitions are properly isolated."""
        # Create two competitions
        comp1 = await comp_repo.create_competition(schemas.CompetitionCreate(name="Comp 1"))
        comp2 = await comp_repo.create_competition(schemas.CompetitionCreate(name="Comp 2"))

        # Create users
        users = []
        for i in range(4):
            user = await user_repo.create_user(
                schemas.UserCreate(username=f"user{i}", email=f"u{i}@test.com", password="pass"),
                f"hash{i}"
            )
            users.append(user)

        # Create matches for each competition
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        matches1 = await match_repo.create_matches([
            FakeMatchPayload(comp1.id, users[0].id, users[1].id, "*")
        ])

        matches2 = await match_repo.create_matches([
            FakeMatchPayload(comp2.id, users[2].id, users[3].id, "*")
        ])

        # Verify matches belong to correct competitions
        assert matches1[0].competition_id == str(comp1.id)
        assert matches2[0].competition_id == str(comp2.id)
        assert matches1[0].competition_id != matches2[0].competition_id