def calculate_elo(rating1: int, rating2: int, result: float, k: int = 32) -> tuple[int, int]:
    """
    Calculate new Elo ratings given ratings of player 1 and 2.
    result = 1.0 (win), 0.5 (draw), 0.0 (loss) for player 1.
    """
    expected1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    expected2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))

    new_rating1 = int(rating1 + k * (result - expected1))
    new_rating2 = int(rating2 + k * ((1.0 - result) - expected2))

    return new_rating1, new_rating2
