"""
Tests for Matches API Endpoints
===============================
Tests all endpoints in routers/matches.py that account for the database engine in use.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO


@pytest.mark.asyncio
async def test_update_match_result_unauthorized(test_client: AsyncClient):
    """Test updating match result without proper authorization."""
    match_update = {
        "result": "1-0",
        "pgn_blueprint": "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"
    }
    response = await test_client.put("/matches/1", json=match_update)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bulk_upload_pgn_unauthorized(test_client: AsyncClient):
    """Test bulk uploading PGN without proper authorization."""
    pgn_content = b"""[Event "Test Game"]
[White "Player1"]
[Black "Player2"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
"""
    files = {"file": ("test.pgn", BytesIO(pgn_content), "application/x-chess-pgn")}
    response = await test_client.post("/matches/bulk-upload", files=files)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_evaluate_match_unauthorized(test_client: AsyncClient):
    """Test evaluating match without authentication."""
    response = await test_client.post("/matches/1/evaluate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_evaluate_match_not_found(test_client: AsyncClient):
    """Test evaluating a non-existent match."""
    # Create a user first
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "secretpassword"}
    )
    assert signup_response.status_code == 200

    # Login to get token
    login_response = await test_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "secretpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Try to evaluate non-existent match
    response = await test_client.post(
        "/matches/999/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_match_comment_unauthorized(test_client: AsyncClient):
    """Test creating a match comment without authentication."""
    comment_data = {"content": "Great game!"}
    response = await test_client.post("/matches/1/comments", json=comment_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_match_comments(test_client: AsyncClient):
    """Test getting comments for a match."""
    response = await test_client.get("/matches/1/comments")
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)


@pytest.mark.asyncio
async def test_get_match_comments_pagination(test_client: AsyncClient):
    """Test getting match comments with pagination."""
    response = await test_client.get("/matches/1/comments?skip=0&limit=10")
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)


# Note: Full integration tests for matches would require:
# 1. Creating competitions and matches through the competition lifecycle
# 2. Admin/organizer users for updating match results
# 3. Actual PGN files for upload and evaluation
# 4. Match comments functionality
#
# These tests focus on the API endpoint structure, authentication, and error handling.
# More comprehensive tests would be integration tests that set up the full match lifecycle.