import pytest
from core.services.chess_service import parse_bulk_pgn, evaluate_pgn_with_stockfish

@pytest.mark.asyncio
async def test_parse_bulk_pgn():
    sample_pgn = '''[Event "FIDE World Cup 2017"]
[Site "Tbilisi GEO"]
[Date "2017.09.09"]
[Round "4.2"]
[White "Carlsen, M."]
[Black "Bu Xiangzhi"]
[Result "1/2-1/2"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 1/2-1/2

[Event "Blitz Tournament"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0
'''
    parsed = await parse_bulk_pgn(sample_pgn)
    assert len(parsed) == 2
    assert parsed[0]["headers"]["White"] == "Carlsen, M."
    assert parsed[1]["headers"]["Event"] == "Blitz Tournament"
    assert len(parsed[1]["moves"]) > 0

@pytest.mark.asyncio
async def test_evaluate_stockfish_missing_gracefully():
    # Because CI or the local environment might entirely lack a stockfish binary, 
    # we expect the try/except block natively bypassing crashes safely.
    res = await evaluate_pgn_with_stockfish("1. e4 e5")
    assert "status" in res
    assert res["status"] in ["error", "success"] # Depending on local install state
