"""
Tests for Match Service
=======================
Tests all functions in core.services.match_service that work regardless of database backend.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from core.services import match_service
from core.schemas import schemas
from core.db import models


class TestMatchService:
    """Test suite for match service functions."""

    @pytest.mark.asyncio
    async def test_update_match_result_success(self):
        """Test successfully updating a match result."""
        mock_repo = AsyncMock()
        mock_match = models.Match(
            id="1", competition_id="1", white_player_id="1", black_player_id="2",
            result=models.MatchResult.PENDING, pgn_blueprint=""
        )
        updated_match = models.Match(
            id="1", competition_id="1", white_player_id="1", black_player_id="2",
            result=models.MatchResult.WHITE_WINS, pgn_blueprint="1. e4 e5"
        )

        mock_repo.get_match.return_value = mock_match
        mock_repo.update_match.return_value = updated_match

        match_data = schemas.MatchUpdate(result=models.MatchResult.WHITE_WINS, pgn_blueprint="1. e4 e5")

        result = await match_service.update_match_result(mock_repo, "1", match_data)

        assert result == updated_match
        mock_repo.get_match.assert_called_once_with("1")
        mock_repo.update_match.assert_called_once_with(mock_match, result=models.MatchResult.WHITE_WINS, pgn_blueprint="1. e4 e5")

    @pytest.mark.asyncio
    async def test_update_match_result_not_found(self):
        """Test updating a non-existent match raises 404."""
        mock_repo = AsyncMock()
        mock_repo.get_match.return_value = None

        match_data = schemas.MatchUpdate(result=models.MatchResult.DRAW)

        with pytest.raises(HTTPException) as exc_info:
            await match_service.update_match_result(mock_repo, "999", match_data)

        assert exc_info.value.status_code == 404
        assert "Match not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_match_result_without_pgn(self):
        """Test updating match result without PGN blueprint."""
        mock_repo = AsyncMock()
        mock_match = models.Match(
            id="1", competition_id="1", white_player_id="1", black_player_id="2",
            result=models.MatchResult.PENDING, pgn_blueprint=""
        )
        updated_match = models.Match(
            id="1", competition_id="1", white_player_id="1", black_player_id="2",
            result=models.MatchResult.DRAW, pgn_blueprint=""
        )

        mock_repo.get_match.return_value = mock_match
        mock_repo.update_match.return_value = updated_match

        match_data = schemas.MatchUpdate(result=models.MatchResult.DRAW)

        result = await match_service.update_match_result(mock_repo, "1", match_data)

        assert result == updated_match
        mock_repo.update_match.assert_called_once_with(mock_match, result=models.MatchResult.DRAW, pgn_blueprint=None)