"""
Tests for Elo Service
=====================
Tests all functions in core.services.elo_service that work regardless of database backend.
"""

import pytest
from core.services import elo_service


class TestEloService:
    """Test suite for Elo service functions."""

    def test_calculate_elo_white_win(self):
        """Test Elo calculation when white wins."""
        rating1, rating2 = 1200, 1300
        result = 1.0  # White wins

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, result)

        # White (player 1) should gain points
        assert new_rating1 > rating1
        # Black (player 2) should lose points
        assert new_rating2 < rating2
        # Total points should be conserved (within rounding)
        assert abs((new_rating1 + new_rating2) - (rating1 + rating2)) <= 1

    def test_calculate_elo_black_win(self):
        """Test Elo calculation when black wins."""
        rating1, rating2 = 1200, 1300
        result = 0.0  # Black wins (white loses)

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, result)

        # White (player 1) should lose points
        assert new_rating1 < rating1
        # Black (player 2) should gain points
        assert new_rating2 > rating2

    def test_calculate_elo_draw(self):
        """Test Elo calculation for a draw."""
        rating1, rating2 = 1200, 1300
        result = 0.5  # Draw

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, result)

        # Both players should have ratings closer to each other
        # Higher rated player loses some points, lower rated gains some
        assert new_rating1 > rating1  # 1200 player gains
        assert new_rating2 < rating2  # 1300 player loses

    def test_calculate_elo_equal_ratings(self):
        """Test Elo calculation with equal starting ratings."""
        rating1, rating2 = 1200, 1200
        result = 1.0  # Player 1 wins

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, result)

        # Winner should gain exactly 16 points (K=32/2)
        assert new_rating1 == 1216
        # Loser should lose exactly 16 points
        assert new_rating2 == 1184

    def test_calculate_elo_custom_k_factor(self):
        """Test Elo calculation with custom K-factor."""
        rating1, rating2 = 1200, 1200

        # Test with K=16 (should result in half the point changes)
        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, 1.0, k=16)

        assert new_rating1 == 1208  # Half of 16
        assert new_rating2 == 1192  # Half of -16

    def test_calculate_elo_large_rating_difference(self):
        """Test Elo calculation with large rating difference."""
        rating1, rating2 = 1000, 1500  # 500 point difference
        result = 1.0  # Lower rated player wins

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, result)

        # Lower rated player should gain significant points
        assert new_rating1 > rating1
        # Higher rated player should lose fewer points
        assert new_rating2 < rating2

        # The lower rated player should gain more than the higher rated loses
        # due to the expected score being much lower for the underdog
        gain = new_rating1 - rating1
        loss = rating2 - new_rating2
        assert gain >= loss  # Allow for rounding differences

    def test_calculate_elo_zero_result(self):
        """Test Elo calculation with 0.0 result (loss)."""
        rating1, rating2 = 1400, 1200

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, 0.0)

        # Player 1 loses to lower rated opponent
        assert new_rating1 < rating1
        # Player 2 gains points
        assert new_rating2 > rating2

    def test_calculate_elo_one_result(self):
        """Test Elo calculation with 1.0 result (win)."""
        rating1, rating2 = 1200, 1400

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, 1.0)

        # Player 1 wins against higher rated opponent
        assert new_rating1 > rating1
        # Player 2 loses points
        assert new_rating2 < rating2

    def test_calculate_elo_half_result(self):
        """Test Elo calculation with 0.5 result (draw)."""
        rating1, rating2 = 1300, 1200

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, 0.5)

        # Both players' ratings should move toward each other
        # Higher rated player loses some rating, lower rated gains some
        assert new_rating1 < rating1
        assert new_rating2 > rating2

    def test_calculate_elo_extreme_ratings(self):
        """Test Elo calculation with extreme rating differences."""
        # Very low vs very high rating
        rating1, rating2 = 500, 2500

        new_rating1, new_rating2 = elo_service.calculate_elo(rating1, rating2, 1.0)

        # Even with huge difference, ratings should change
        assert new_rating1 > rating1
        assert new_rating2 < rating2

        # The low rated player should gain close to maximum points
        # The high rated player should lose minimal points
        gain = new_rating1 - rating1
        loss = rating2 - new_rating2
        assert gain >= loss  # Allow for rounding differences