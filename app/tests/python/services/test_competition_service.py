"""
Tests for Competition Service
=============================
Tests all functions in core.services.competition_service that work regardless of database backend.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from core.services import competition_service
from core.schemas import schemas
from core.db import models


class TestCompetitionService:
    """Test suite for competition service functions."""

    @pytest.mark.asyncio
    async def test_get_competitions(self):
        """Test retrieving paginated list of competitions."""
        mock_repo = AsyncMock()
        mock_comps = [
            schemas.Competition(id="1", name="Tournament 1", description="Desc 1", max_participants=10, status="pending"),
            schemas.Competition(id="2", name="Tournament 2", description="Desc 2", max_participants=8, status="active")
        ]
        mock_repo.get_competitions.return_value = mock_comps

        result = await competition_service.get_competitions(mock_repo, skip=0, limit=10)

        assert result == mock_comps
        mock_repo.get_competitions.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_get_competition_success(self):
        """Test retrieving a specific competition successfully."""
        mock_repo = AsyncMock()
        mock_comp = schemas.Competition(id="1", name="Tournament 1", description="Desc 1", max_participants=10, status="pending")
        mock_repo.get_competition.return_value = mock_comp

        result = await competition_service.get_competition(mock_repo, "1")

        assert result == mock_comp
        mock_repo.get_competition.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_get_competition_not_found(self):
        """Test retrieving a non-existent competition raises 404."""
        mock_repo = AsyncMock()
        mock_repo.get_competition.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await competition_service.get_competition(mock_repo, "999")

        assert exc_info.value.status_code == 404
        assert "Competition not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_competition(self):
        """Test creating a new competition."""
        mock_repo = AsyncMock()
        mock_comp = schemas.Competition(id="1", name="New Tournament", description="New Desc", max_participants=16, status="pending")
        mock_repo.create_competition.return_value = mock_comp

        comp_data = schemas.CompetitionCreate(name="New Tournament", description="New Desc", max_participants=16)

        result = await competition_service.create_competition(mock_repo, comp_data)

        assert result == mock_comp
        mock_repo.create_competition.assert_called_once_with(comp_data)

    @pytest.mark.asyncio
    async def test_join_competition_success(self):
        """Test successfully joining a competition."""
        mock_repo = AsyncMock()
        mock_comp = schemas.Competition(id="1", name="Tournament", description="Desc", max_participants=10, status="pending", players=[])
        mock_user = models.User(id="2", username="player", email="player@test.com", hashed_password="hash", elo=1200)

        mock_repo.get_competition.return_value = mock_comp
        mock_repo.add_player_to_competition.return_value = mock_comp

        result = await competition_service.join_competition(mock_repo, "1", mock_user)

        assert result == mock_comp
        mock_repo.get_competition.assert_called_once_with("1")
        mock_repo.add_player_to_competition.assert_called_once_with(mock_comp, mock_user)

    @pytest.mark.asyncio
    async def test_get_standings_empty_competition(self):
        """Test getting standings for competition with no matches."""
        mock_repo = AsyncMock()
        mock_comp = schemas.Competition(
            id="1", name="Tournament", format="round_robin", status="active",
            players=[
                schemas.User(id="1", username="p1", email="p1@test.com", role="player", elo=1200),
                schemas.User(id="2", username="p2", email="p2@test.com", role="player", elo=1300)
            ],
            matches=[]
        )
        mock_repo.get_competition.return_value = mock_comp

        result = await competition_service.get_standings(mock_repo, "1")

        assert len(result) == 2
        # Both players should have 0 points, 0 matches played
        for standing in result:
            assert standing["points"] == 0.0
            assert standing["matches_played"] == 0
            assert standing["wins"] == 0
            assert standing["draws"] == 0
            assert standing["losses"] == 0

    @pytest.mark.asyncio
    async def test_get_standings_with_matches(self):
        """Test getting standings for competition with completed matches."""
        mock_repo = AsyncMock()

        players = [
            schemas.User(id="1", username="p1", email="p1@test.com", role="player", elo=1200),
            schemas.User(id="2", username="p2", email="p2@test.com", role="player", elo=1300),
            schemas.User(id="3", username="p3", email="p3@test.com", role="player", elo=1100)
        ]

        matches = [
            schemas.Match(id="1", competition_id="1", white_player_id="1", black_player_id="2", result=models.MatchResult.WHITE_WINS, pgn_blueprint=""),
            schemas.Match(id="2", competition_id="1", white_player_id="1", black_player_id="3", result=models.MatchResult.DRAW, pgn_blueprint=""),
            schemas.Match(id="3", competition_id="1", white_player_id="2", black_player_id="3", result=models.MatchResult.BLACK_WINS, pgn_blueprint="")
        ]

        mock_comp = schemas.Competition(
            id="1", name="Tournament", format="round_robin", status="active",
            players=players, matches=matches
        )
        mock_repo.get_competition.return_value = mock_comp

        result = await competition_service.get_standings(mock_repo, "1")

        assert len(result) == 3

        # Find standings by player ID
        standings_by_id = {s["player"].id: s for s in result}

        # Player 1: 1 win (vs P2) + 1 draw (vs P3) = 1.5 points, 2 matches
        p1_standing = standings_by_id["1"]
        assert p1_standing["points"] == 1.5
        assert p1_standing["matches_played"] == 2
        assert p1_standing["wins"] == 1
        assert p1_standing["draws"] == 1
        assert p1_standing["losses"] == 0

        # Player 2: 1 loss (vs P1) + 1 loss (vs P3) = 0 points, 2 matches
        p2_standing = standings_by_id["2"]
        assert p2_standing["points"] == 0.0
        assert p2_standing["matches_played"] == 2
        assert p2_standing["wins"] == 0
        assert p2_standing["draws"] == 0
        assert p2_standing["losses"] == 2

        # Player 3: 1 draw (vs P1) + 1 win (vs P2) = 1.5 points, 2 matches
        p3_standing = standings_by_id["3"]
        assert p3_standing["points"] == 1.5
        assert p3_standing["matches_played"] == 2
        assert p3_standing["wins"] == 1
        assert p3_standing["draws"] == 1
        assert p3_standing["losses"] == 0

    @pytest.mark.asyncio
    async def test_generate_matches_round_robin(self):
        """Test generating Round Robin matches for a competition."""
        mock_comp_repo = AsyncMock()
        mock_match_repo = AsyncMock()

        players = [
            schemas.User(id="1", username="p1", email="p1@test.com", role="player", elo=1200),
            schemas.User(id="2", username="p2", email="p2@test.com", role="player", elo=1300),
            schemas.User(id="3", username="p3", email="p3@test.com", role="player", elo=1100)
        ]

        mock_comp = schemas.Competition(
            id="1", name="Tournament", description="Desc", max_participants=4, status="pending",
            players=players, matches=[]
        )

        mock_comp_repo.get_competition.return_value = mock_comp
        mock_match_repo.create_matches.return_value = []

        result = await competition_service.generate_matches(mock_comp_repo, mock_match_repo, "1")

        # Should generate 3 matches for 3 players (n*(n-1)/2)
        assert "Generated 3 matches" in result["message"]
        mock_comp_repo.update_competition_status.assert_called_once_with(mock_comp, "active")
        mock_match_repo.create_matches.assert_called_once()

        # Verify the matches that were created
        call_args = mock_match_repo.create_matches.call_args[0][0]
        assert len(call_args) == 3

        # Check that all player pairs are represented
        match_pairs = {(m.white_player_id, m.black_player_id) for m in call_args}
        expected_pairs = {("1", "2"), ("1", "3"), ("2", "3")}
        assert match_pairs == expected_pairs

    @pytest.mark.asyncio
    async def test_generate_matches_insufficient_players(self):
        """Test generating matches fails with insufficient players."""
        mock_comp_repo = AsyncMock()
        mock_match_repo = AsyncMock()

        mock_comp = schemas.Competition(
            id="1", name="Tournament", description="Desc", max_participants=4, status="pending",
            players=[schemas.User(id="1", username="p1", email="p1@test.com", role="player", elo=1200)],
            matches=[]
        )

        mock_comp_repo.get_competition.return_value = mock_comp

        with pytest.raises(HTTPException) as exc_info:
            await competition_service.generate_matches(mock_comp_repo, mock_match_repo, "1")

        assert exc_info.value.status_code == 400
        assert "Not enough players" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_finish_competition(self):
        """Test finishing a competition and updating Elo ratings."""
        mock_comp_repo = AsyncMock()
        mock_user_repo = AsyncMock()

        players = [
            schemas.User(id="1", username="p1", email="p1@test.com", role="player", elo=1200),
            schemas.User(id="2", username="p2", email="p2@test.com", role="player", elo=1300)
        ]

        matches = [
            schemas.Match(id="1", competition_id="1", white_player_id="1", black_player_id="2",
                        result=models.MatchResult.WHITE_WINS, pgn_blueprint="")
        ]

        mock_comp = schemas.Competition(
            id="1", name="Tournament", description="Desc", max_participants=4, status="active",
            players=players, matches=matches
        )

        mock_comp_repo.get_competition.return_value = mock_comp

        result = await competition_service.finish_competition(mock_comp_repo, mock_user_repo, "1")

        assert "Competition finalized" in result["message"]
        mock_comp_repo.update_competition_status.assert_called_once_with(mock_comp, "finished")

        # Verify Elo updates were called for both players
        assert mock_user_repo.update_user_elo.call_count == 2
        # The exact Elo calculations depend on the implementation, but both players should be updated
        call_args_list = mock_user_repo.update_user_elo.call_args_list
        updated_player_ids = {call[0][0] for call in call_args_list}
        assert updated_player_ids == {"1", "2"}

    @pytest.mark.asyncio
    async def test_finish_competition_already_finished(self):
        """Test finishing an already finished competition fails."""
        mock_comp_repo = AsyncMock()
        mock_user_repo = AsyncMock()

        mock_comp = schemas.Competition(
            id="1", name="Tournament", description="Desc", max_participants=4, status="finished",
            players=[], matches=[]
        )

        mock_comp_repo.get_competition.return_value = mock_comp

        with pytest.raises(HTTPException) as exc_info:
            await competition_service.finish_competition(mock_comp_repo, mock_user_repo, "1")

        assert exc_info.value.status_code == 400
        assert "already marked finished" in exc_info.value.detail