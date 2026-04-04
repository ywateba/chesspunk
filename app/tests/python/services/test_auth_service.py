"""
Tests for Authentication Service
===============================
Tests all functions in core.services.auth_service that work regardless of database backend.
"""

import pytest
from unittest.mock import AsyncMock, patch
from core.services import auth_service
from core.schemas import schemas
from core.db import models


class TestAuthService:
    """Test suite for authentication service functions."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_or_username_by_email(self):
        """Test finding user by email."""
        mock_repo = AsyncMock()
        mock_user = models.User(id="1", username="testuser", email="test@example.com", hashed_password="hash", elo=1200)
        mock_repo.get_user_by_email.return_value = mock_user
        mock_repo.get_user_by_username.return_value = None

        result = await auth_service.get_user_by_email_or_username(mock_repo, "test@example.com")

        assert result == mock_user
        mock_repo.get_user_by_email.assert_called_once_with("test@example.com")
        mock_repo.get_user_by_username.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_by_email_or_username_by_username(self):
        """Test finding user by username when email lookup fails."""
        mock_repo = AsyncMock()
        mock_user = models.User(id="1", username="testuser", email="test@example.com", hashed_password="hash", elo=1200)
        mock_repo.get_user_by_email.return_value = None
        mock_repo.get_user_by_username.return_value = mock_user

        result = await auth_service.get_user_by_email_or_username(mock_repo, "testuser")

        assert result == mock_user
        mock_repo.get_user_by_email.assert_called_once_with("testuser")
        mock_repo.get_user_by_username.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_get_user_by_email_or_username_not_found(self):
        """Test user not found by either email or username."""
        mock_repo = AsyncMock()
        mock_repo.get_user_by_email.return_value = None
        mock_repo.get_user_by_username.return_value = None

        result = await auth_service.get_user_by_email_or_username(mock_repo, "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test creating a new user with password hashing."""
        mock_repo = AsyncMock()
        mock_user = models.User(id="1", username="testuser", email="test@example.com", hashed_password="hashed_pass", elo=1200)
        mock_repo.create_user.return_value = mock_user

        user_data = schemas.UserCreate(username="testuser", email="test@example.com", password="password123")

        result = await auth_service.create_user(mock_repo, user_data)

        assert result == mock_user
        # Verify that create_user was called with hashed password (we can't easily mock the hash function)
        assert mock_repo.create_user.called
        call_args = mock_repo.create_user.call_args
        assert call_args[0][0] == user_data  # First argument should be user data
        # Second argument should be hashed password (string)
        assert isinstance(call_args[0][1], str)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        mock_repo = AsyncMock()
        mock_user = models.User(id="1", username="testuser", email="test@example.com", hashed_password="$2b$12$1NL2.RkHdTLHzJXJRG0b1epHmbH7es3Fb31OhrmpZ9e9gCeVXCF8O", elo=1200)
        mock_repo.get_user_by_email.return_value = mock_user
        mock_repo.get_user_by_username.return_value = None

        with patch('core.auth.utils.verify_password', return_value=True):
            result = await auth_service.authenticate_user(mock_repo, "test@example.com", "correct_password")

            assert result == mock_user
            mock_repo.get_user_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authentication failure with wrong password."""
        mock_repo = AsyncMock()
        mock_user = models.User(id="1", username="testuser", email="test@example.com", hashed_password="$2b$12$1NL2.RkHdTLHzJXJRG0b1epHmbH7es3Fb31OhrmpZ9e9gCeVXCF8O", elo=1200)
        mock_repo.get_user_by_email.return_value = mock_user

        with patch('core.auth.utils.verify_password', return_value=False):
            result = await auth_service.authenticate_user(mock_repo, "test@example.com", "wrong_password")

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test authentication failure when user doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo.get_user_by_email.return_value = None
        mock_repo.get_user_by_username.return_value = None

        result = await auth_service.authenticate_user(mock_repo, "nonexistent", "password")

        assert result is None