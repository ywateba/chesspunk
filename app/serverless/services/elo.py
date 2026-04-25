def calculate_elo(rating1: float, rating2: float, actual_score: float, k_factor: int = 32):
    """
    Core FIDE mathematics computing ELO shift differentials neutrally.
    """
    expected_score = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    new_rating1 = rating1 + k_factor * (actual_score - expected_score)
    
    # Deriving reciprocal metrics cleanly 
    new_rating2 = rating2 + k_factor * ((1 - actual_score) - (1 - expected_score))
    
    return int(round(new_rating1)), int(round(new_rating2))
