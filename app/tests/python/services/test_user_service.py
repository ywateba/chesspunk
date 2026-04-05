"""
Tests for User Service
======================
Tests all functions in core.services.user_service that work regardless of database backend.
"""

import pytest
from unittest.mock import AsyncMock
from core.services import user_service
from core.schemas import schemas


class TestUserService:
    """Test suite for user service functions."""

    @pytest.mark.asyncio
    async def test_get_users_list(self):
        """Test retrieving paginated list of users."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_users = [
            schemas.User(id="1", username="user1", email="user1@test.com", elo=1200),
            schemas.User(id="2", username="user2", email="user2@test.com", elo=1300)
        ]
        mock_repo.get_users.return_value = mock_users

        # Test service function
        result = await user_service.get_users_list(mock_repo, skip=0, limit=10)

        # Assertions
        assert result == mock_users
        mock_repo.get_users.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_get_users_list_with_pagination(self):
        """Test retrieving users with custom pagination."""
        mock_repo = AsyncMock()
        mock_repo.get_users.return_value = []

        result = await user_service.get_users_list(mock_repo, skip=20, limit=5)

        assert result == []
        mock_repo.get_users.assert_called_once_with(skip=20, limit=5)