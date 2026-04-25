from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from serverless.handlers import users, competitions

app = APIGatewayHttpResolver()

# Helper for handling NotFound errors
def not_found(msg="Resource not found"):
    return Response(status_code=404, body={"error": msg})

# Helper for catching bad requests
def bad_request(msg):
    return Response(status_code=400, body={"error": msg})

# --- Users ---
@app.get("/users")
def list_users_route():
    return users.list_users()

@app.post("/users")
def create_user_route():
    try:
        return users.create_user(app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.get("/users/<user_id>")
def get_user_route(user_id: str):
    user = users.get_user(user_id)
    return user if user else not_found("User not found")

@app.put("/users/<user_id>")
def update_user_route(user_id: str):
    try:
        return users.update_user(user_id, app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.delete("/users/<user_id>")
def delete_user_route(user_id: str):
    return users.delete_user(user_id)


# --- Competitions ---
@app.get("/competitions")
def list_competitions_route():
    return competitions.list_competitions()

@app.post("/competitions")
def create_competition_route():
    try:
        return competitions.create_competition(app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.get("/competitions/<comp_id>")
def get_competition_route(comp_id: str):
    comp = competitions.get_competition(comp_id)
    return comp if comp else not_found("Competition not found")

@app.put("/competitions/<comp_id>/status")
def update_comp_status_route(comp_id: str):
    try:
        return competitions.update_status(comp_id, app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.post("/competitions/<comp_id>/players")
def add_player_route(comp_id: str):
    try:
        return competitions.add_player(comp_id, app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.post("/competitions/<comp_id>/matches/generate")
def generate_matches_route(comp_id: str):
    try:
        res = competitions.generate_matches(comp_id)
        return res if res else not_found("Competition not found")
    except Exception as e:
        return bad_request(str(e))

@app.get("/competitions/<comp_id>/standings")
def get_standings_route(comp_id: str):
    res = competitions.get_standings(comp_id)
    return res if res is not None else not_found("Competition not found")

@app.post("/competitions/<comp_id>/finish")
def finish_competition_route(comp_id: str):
    try:
        res = competitions.finish_competition(comp_id)
        return res if res else not_found("Competition not found")
    except Exception as e:
        return bad_request(str(e))


from serverless.handlers import community, social, matches

# --- Communities ---
@app.get("/communities")
def list_communities_route():
    return community.list_communities()

@app.post("/communities")
def create_community_route():
    try:
        return community.create_community(app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.get("/communities/<comm_id>")
def get_community_route(comm_id: str):
    comm = community.get_community(comm_id)
    return comm if comm else not_found("Community not found")

@app.post("/communities/<comm_id>/members")
def add_member_route(comm_id: str):
    try:
        return community.add_member(comm_id, app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

# --- Social & Posts ---
@app.get("/social")
def list_posts_route():
    return social.list_posts()

@app.post("/social")
def create_post_route():
    try:
        return social.create_post(app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.get("/social/<post_id>")
def get_post_route(post_id: str):
    post = social.get_post(post_id)
    return post if post else not_found("Post not found")

@app.post("/social/<post_id>/comments")
def create_comment_route(post_id: str):
    try:
        return social.create_comment(post_id, app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

# --- Matches ---
@app.get("/matches/<match_id>")
def get_match_route(match_id: str):
    match = matches.get_match(match_id)
    return match if match else not_found("Match not found")

@app.put("/matches/<match_id>")
def update_match_route(match_id: str):
    try:
        return matches.update_match_result(match_id, app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

@app.post("/matches/bulk-upload")
def bulk_upload_route():
    try:
        return matches.bulk_upload_pgn(app.current_event.json_body)
    except Exception as e:
        return bad_request(str(e))

from serverless.logger import logger

def lambda_handler(event, context):
    """
    Main entrypoint for API Gateway, routing via aws-lambda-powertools!
    """
    logger.info(f"Incoming Request: {event.get('routeKey', event.get('httpMethod', 'Unknown'))} {event.get('rawPath', '')}")
    return app.resolve(event, context)
