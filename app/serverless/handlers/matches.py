from serverless.dynamodb import get_table
from serverless.services.chess import parse_bulk_pgn
from serverless.logger import logger

def get_match(match_id: str):
    logger.debug(f"Fetching match: {match_id}")
    table = get_table('Matches')
    return table.get_item(Key={'id': match_id}).get('Item')

def update_match_result(match_id: str, body: dict):
    logger.info(f"Updating match {match_id} result payload.")
    result = body.get('result')
    if result not in ["WHITE_WINS", "BLACK_WINS", "DRAW", "PENDING"]:
        logger.error(f"Invalid match result specified: {result}")
        raise ValueError("Invalid result formatting")
        
    table = get_table('Matches')
    
    update_expr = "SET #res = :result"
    expr_names = {"#res": "result"}
    expr_attrs = {":result": result}
    
    if "pgn" in body:
        update_expr += ", pgn = :pgn"
        expr_attrs[":pgn"] = body["pgn"]
        
    response = table.update_item(
        Key={'id': match_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_attrs,
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')

from serverless.services.chess import parse_bulk_pgn

def bulk_upload_pgn(body: dict):
    logger.info("Executing Bulk PGN Upload Pipeline.")
    pgn_string = body.get('pgn')
    if not pgn_string:
        logger.error("Missing PGN payload in bulk upload.")
        raise ValueError("Missing pgn string payload")
        
    logger.debug(f"Parsing PGN String length: {len(pgn_string)}")
    parsed_games = parse_bulk_pgn(pgn_string)
    logger.info(f"Successfully evaluated {len(parsed_games)} complete PGN blueprints.")
    
    return {
        "message": f"Successfully parsed {len(parsed_games)} games",
        "games_metadata": [
            {
                "event": g["headers"].get("Event", "?"), 
                "white": g["headers"].get("White", "?"), 
                "black": g["headers"].get("Black", "?")
            } for g in parsed_games
        ]
    }
