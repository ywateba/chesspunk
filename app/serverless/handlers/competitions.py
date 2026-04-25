import uuid
from boto3.dynamodb.conditions import Attr
from serverless.dynamodb import get_table
from serverless.services.elo import calculate_elo
from serverless.logger import logger

def create_competition(body: dict):
    name = body.get('name')
    if not name:
        raise ValueError("Missing name parameter")
        
    comp_id = str(uuid.uuid4())
    table = get_table('Competitions')
    
    item = {
        'id': comp_id,
        'name': name,
        'description': body.get('description', ''),
        'status': 'open',
        'players': [],
        'matches': []
    }
    table.put_item(Item=item)
    logger.debug(f"Competition {comp_id} successfully persisted.")
    return item

def get_competition(comp_id: str):
    logger.debug(f"Fetching competition: {comp_id}")
    table = get_table('Competitions')
    return table.get_item(Key={'id': comp_id}).get('Item')

def list_competitions():
    logger.debug("Scanning all competitions")
    table = get_table('Competitions')
    return table.scan().get('Items', [])

def update_status(comp_id: str, body: dict):
    status = body.get('status')
    if not status:
        raise ValueError("Missing status parameter")
        
    table = get_table('Competitions')
    response = table.update_item(
        Key={'id': comp_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": status},
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')

def add_player(comp_id: str, body: dict):
    player_id = body.get('player_id')
    if not player_id:
        raise ValueError("Missing player_id parameter")
        
    table = get_table('Competitions')
    response = table.update_item(
        Key={'id': comp_id},
        UpdateExpression="SET players = list_append(if_not_exists(players, :empty_list), :player)",
        ExpressionAttributeValues={
            ":player": [player_id],
            ":empty_list": []
        },
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')

def get_standings(comp_id: str):
    comp = get_competition(comp_id)
    if not comp: return None
        
    matches_table = get_table('Matches')
    scan_res = matches_table.scan(FilterExpression=Attr('competition_id').eq(comp_id))
    matches = scan_res.get('Items', [])
    
    standings = {}
    for player_id in comp.get('players', []):
        standings[player_id] = {
            "player_id": player_id, "points": 0.0, "buchholz": 0.0,
            "matches_played": 0, "wins": 0, "draws": 0, "losses": 0
        }
        
    for match in matches:
        if match.get('result', 'PENDING') == 'PENDING': continue
        w_id = match.get('white_player_id')
        b_id = match.get('black_player_id')
        res = match.get('result')
        
        if w_id in standings and b_id in standings:
            standings[w_id]["matches_played"] += 1
            standings[b_id]["matches_played"] += 1
            if res == 'WHITE_WINS':
                standings[w_id]["wins"] += 1; standings[w_id]["points"] += 1.0
                standings[b_id]["losses"] += 1
            elif res == 'BLACK_WINS':
                standings[b_id]["wins"] += 1; standings[b_id]["points"] += 1.0
                standings[w_id]["losses"] += 1
            elif res == 'DRAW':
                standings[w_id]["draws"] += 1; standings[w_id]["points"] += 0.5
                standings[b_id]["draws"] += 1; standings[b_id]["points"] += 0.5
                
    for match in matches:
        if match.get('result', 'PENDING') != 'PENDING':
            w_id, b_id = match.get('white_player_id'), match.get('black_player_id')
            if w_id in standings and b_id in standings:
                standings[w_id]["buchholz"] += standings[b_id]["points"]
                standings[b_id]["buchholz"] += standings[w_id]["points"]
                
    return sorted(standings.values(), key=lambda x: (x["points"], x["buchholz"], x["wins"]), reverse=True)

def generate_matches(comp_id: str):
    logger.info(f"Attempting to generate matches for competition: {comp_id}")
    comp = get_competition(comp_id)
    if not comp: 
        logger.warning(f"Generate Matches aborted: Competition {comp_id} not found")
        return None
        
    players = comp.get('players', [])
    if len(players) < 2: 
        logger.error(f"Cannot generate matches: Only {len(players)} players found.")
        raise ValueError("Not enough players")
        
    matches_table = get_table('Matches')
    created = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            match_item = {
                "id": str(uuid.uuid4()), "competition_id": comp_id,
                "white_player_id": players[i], "black_player_id": players[j],
                "result": "PENDING"
            }
            matches_table.put_item(Item=match_item)
            created.append(match_item)
            
    update_status(comp_id, {"status": "active"})
    logger.info(f"Successfully generated {len(created)} matches for competition {comp_id}")
    return {"message": f"Generated {len(created)} matches", "matches": created}

def finish_competition(comp_id: str):
    logger.info(f"Finalizing competition: {comp_id}")
    comp = get_competition(comp_id)
    if not comp: return None
    if comp.get('status') == 'finished': 
        logger.warning(f"Competition {comp_id} is already finished.")
        raise ValueError("Already finished")
        
    matches_table = get_table('Matches')
    matches = matches_table.scan(FilterExpression=Attr('competition_id').eq(comp_id)).get('Items', [])
    users_table = get_table('Users')
    
    players_data = {}
    for p_id in comp.get('players', []):
        u_res = users_table.get_item(Key={'id': p_id})
        if 'Item' in u_res:
            players_data[p_id] = u_res['Item']
            if 'elo' not in players_data[p_id]: players_data[p_id]['elo'] = 1200
                
    for match in matches:
        res = match.get('result', 'PENDING')
        if res != 'PENDING':
            w_id, b_id = match.get('white_player_id'), match.get('black_player_id')
            if w_id in players_data and b_id in players_data:
                score_map = {"WHITE_WINS": 1.0, "BLACK_WINS": 0.0, "DRAW": 0.5}
                new_w, new_b = calculate_elo(float(players_data[w_id]['elo']), float(players_data[b_id]['elo']), score_map[res])
                players_data[w_id]['elo'] = new_w
                players_data[b_id]['elo'] = new_b
                
    for p_id, data in players_data.items():
        users_table.update_item(
            Key={'id': p_id},
            UpdateExpression="SET elo = :elo", ExpressionAttributeValues={":elo": data['elo']}
        )
    update_status(comp_id, {"status": "finished"})
    return {"message": "Competition finalized and global ELO ratings synchronized."}
