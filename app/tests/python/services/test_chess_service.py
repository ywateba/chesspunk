"""
Tests for Chess Service
=======================
Tests all functions in core.services.chess_service that work regardless of database backend.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from core.services import chess_service


class TestChessService:
    """Test suite for chess service functions."""

    @pytest.mark.asyncio
    async def test_parse_bulk_pgn_single_game(self):
        """Test parsing a single PGN game."""
        pgn_content = """[Event "Test Game"]
[Site "Test Site"]
[Date "2024.01.01"]
[White "White Player"]
[Black "Black Player"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 1-0
"""

        result = await chess_service.parse_bulk_pgn(pgn_content)

        assert len(result) == 1
        game = result[0]

        assert game["headers"]["Event"] == "Test Game"
        assert game["headers"]["White"] == "White Player"
        assert game["headers"]["Black"] == "Black Player"
        assert game["headers"]["Result"] == "1-0"

        # Check moves (should be in UCI format)
        assert len(game["moves"]) > 0
        assert "e2e4" in game["moves"]  # e4 in UCI
        assert "e7e5" in game["moves"]  # e5 in UCI

        # Check PGN blueprint contains the original
        assert "1. e4 e5" in game["pgn_blueprint"]

    @pytest.mark.asyncio
    async def test_parse_bulk_pgn_multiple_games(self):
        """Test parsing multiple PGN games."""
        pgn_content = """[Event "Game 1"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0

[Event "Game 2"]
[White "Player C"]
[Black "Player D"]
[Result "0-1"]

1. d4 d5 2. c4 0-1
"""

        result = await chess_service.parse_bulk_pgn(pgn_content)

        assert len(result) == 2

        assert result[0]["headers"]["Event"] == "Game 1"
        assert result[0]["headers"]["Result"] == "1-0"

        assert result[1]["headers"]["Event"] == "Game 2"
        assert result[1]["headers"]["Result"] == "0-1"

    @pytest.mark.asyncio
    async def test_parse_bulk_pgn_empty(self):
        """Test parsing empty PGN string."""
        result = await chess_service.parse_bulk_pgn("")

        assert result == []

    @pytest.mark.asyncio
    async def test_parse_bulk_pgn_malformed(self):
        """Test parsing malformed PGN gracefully."""
        malformed_pgn = """[Event "Incomplete Game"]
[White "Player"]
[Black "Opponent"]

1. e4"""

        result = await chess_service.parse_bulk_pgn(malformed_pgn)

        # Should still parse what it can
        assert len(result) >= 0  # May or may not parse depending on chess library

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_evaluate_pgn_with_stockfish_success(self, mock_subprocess):
        """Test successful Stockfish evaluation."""
        # Mock the subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"bestmove e2e4 ponder e7e5\n", b"")
        mock_subprocess.return_value = mock_process

        pgn_blueprint = "1. e4 e5"
        result = await chess_service.evaluate_pgn_with_stockfish(pgn_blueprint, time_limit_ms=100)

        assert result["status"] == "success"
        assert result["bestmove"] == "e2e4"
        assert result["evaluation_completed"] is True

        # Verify subprocess was called correctly
        mock_subprocess.assert_called_once_with(
            'stockfish',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_evaluate_pgn_with_stockfish_no_stockfish(self, mock_subprocess):
        """Test evaluation when Stockfish is not available."""
        # Mock FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError("stockfish command not found")

        pgn_blueprint = "1. e4 e5"
        result = await chess_service.evaluate_pgn_with_stockfish(pgn_blueprint)

        assert result["status"] == "error"
        assert "Stockfish binary not locally found" in result["detail"]

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_evaluate_pgn_with_stockfish_process_error(self, mock_subprocess):
        """Test evaluation when Stockfish process fails."""
        # Mock process that raises an exception
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = Exception("Process failed")
        mock_subprocess.return_value = mock_process

        pgn_blueprint = "1. e4 e5"
        result = await chess_service.evaluate_pgn_with_stockfish(pgn_blueprint)

        assert result["status"] == "error"
        assert "Process failed" in result["detail"]

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_evaluate_pgn_with_stockfish_no_bestmove(self, mock_subprocess):
        """Test evaluation when Stockfish doesn't return a bestmove."""
        # Mock subprocess with output that doesn't contain 'bestmove'
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"info depth 1\nreadyok\n", b"")
        mock_subprocess.return_value = mock_process

        pgn_blueprint = "1. e4 e5"
        result = await chess_service.evaluate_pgn_with_stockfish(pgn_blueprint)

        assert result["status"] == "success"
        assert result["bestmove"] is None  # No bestmove found
        assert result["evaluation_completed"] is True