"""
Tests for Matches API Endpoints
===============================
Tests all endpoints in routers/matches.py that account for the database engine in use.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import AsyncMock
from core.db import models
from core.services import match_service
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


@pytest.mark.asyncio
async def test_update_match_result_authorized(test_client: AsyncClient, db_session: AsyncSession):
    """Test updating a match result with proper authorization."""
    # Create organizer user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "adminuser", "email": "admin@example.com", "password": "secretpass"}
    )
    assert signup_response.status_code == 200

    res = await db_session.execute(select(models.User).where(models.User.username == "adminuser"))
    admin_user = res.scalars().first()
    admin_user.role = "admin"
    await db_session.commit()

    # Create second user
    await test_client.post(
        "/auth/signup",
        json={"username": "player2", "email": "player2@example.com", "password": "secretpass"}
    )

    token_response = await test_client.post(
        "/auth/login",
        data={"username": "adminuser", "password": "secretpass"}
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    # Create competition via API
    comp_response = await test_client.post(
        "/competitions/",
        json={"name": "Match Update Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert comp_response.status_code == 200
    comp_id = comp_response.json()["id"]

    # Join competition with both players
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {token}"})
    
    token2_response = await test_client.post(
        "/auth/login",
        data={"username": "player2", "password": "secretpass"}
    )
    token2 = token2_response.json()["access_token"]
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {token2}"})

    # Generate matches
    gen_response = await test_client.post(
        f"/competitions/{comp_id}/generate-matches",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert gen_response.status_code == 200

    # Get match from competition
    comp_details = await test_client.get(f"/competitions/{comp_id}")
    assert comp_details.status_code == 200
    matches = comp_details.json()["matches"]
    assert len(matches) == 1
    match_id = matches[0]["id"]

    # Update match result
    response = await test_client.put(
        f"/matches/{match_id}",
        json={"result": "1-0", "pgn_blueprint": "1. e4 e5 *"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "1-0"
    assert payload["pgn_blueprint"] == "1. e4 e5 *"


@pytest.mark.asyncio
async def test_evaluate_match_authorized(test_client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Test evaluating a match via the evaluate endpoint."""
    # Create organizer user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "evaluser", "email": "eval@example.com", "password": "secretpass"}
    )
    assert signup_response.status_code == 200

    res = await db_session.execute(select(models.User).where(models.User.username == "evaluser"))
    user = res.scalars().first()
    user.role = "organizer"
    await db_session.commit()

    # Create second user
    await test_client.post(
        "/auth/signup",
        json={"username": "player2", "email": "player2@example.com", "password": "secretpass"}
    )

    login_response = await test_client.post(
        "/auth/login",
        data={"username": "evaluser", "password": "secretpass"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create competition via API
    comp_response = await test_client.post(
        "/competitions/",
        json={"name": "Evaluation Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert comp_response.status_code == 200
    comp_id = comp_response.json()["id"]

    # Join competition with both players
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {token}"})
    
    token2_response = await test_client.post(
        "/auth/login",
        data={"username": "player2", "password": "secretpass"}
    )
    token2 = token2_response.json()["access_token"]
    await test_client.post(f"/competitions/{comp_id}/join", headers={"Authorization": f"Bearer {token2}"})

    # Generate matches
    gen_response = await test_client.post(
        f"/competitions/{comp_id}/generate-matches",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert gen_response.status_code == 200

    # Get match from competition
    comp_details = await test_client.get(f"/competitions/{comp_id}")
    assert comp_details.status_code == 200
    matches = comp_details.json()["matches"]
    assert len(matches) == 1
    match_id = matches[0]["id"]

    # Update match with PGN first
    await test_client.put(
        f"/matches/{match_id}",
        json={"result": "1-0", "pgn_blueprint": "1. e4 e5 *"},
        headers={"Authorization": f"Bearer {token}"}
    )

    mock_eval = AsyncMock(return_value={"bestmove": "e4"})
    monkeypatch.setattr(match_service, "evaluate_pgn_with_stockfish", mock_eval)

    response = await test_client.post(
        f"/matches/{match_id}/evaluate",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {"match_id": match_id, "evaluation": {"bestmove": "e4"}}


# Note: Full integration tests for matches would require:
# 1. Creating competitions and matches through the competition lifecycle
# 2. Admin/organizer users for updating match results
# 3. Actual PGN files for upload and evaluation
# 4. Match comments functionality
#
# These tests focus on the API endpoint structure, authentication, and error handling.
# More comprehensive tests would be integration tests that set up the full match lifecycle.