import chess.pgn
import io
from typing import List, Dict, Any

def parse_bulk_pgn(pgn_string: str) -> List[Dict[str, Any]]:
    """
    Synchronously iterates through dense multi-game PGN payloads extracting sequential structural metadata cleanly.
    """
    pgn_io = io.StringIO(pgn_string)
    parsed_games = []
    
    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
            
        headers = dict(game.headers)
        moves = [move.uci() for move in game.mainline_moves()]
        
        parsed_games.append({
            "headers": headers,
            "moves": moves,
            "pgn_blueprint": str(game)
        })
        
    return parsed_games
