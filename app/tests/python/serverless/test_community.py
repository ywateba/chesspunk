import json
from serverless.handlers.community import create_community_handler, get_community_handler

def test_create_and_get_community():
    create_event = {
        "body": json.dumps({
            "name": "Chess Masters",
            "owner_id": "user123"
        })
    }
    
    response = create_community_handler(create_event, None)
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert body["name"] == "Chess Masters"
    
    comm_id = body["id"]
    
    get_event = {
        "pathParameters": {"comm_id": comm_id}
    }
    get_response = get_community_handler(get_event, None)
    assert get_response["statusCode"] == 200
    
    get_body = json.loads(get_response["body"])
    assert get_body["id"] == comm_id
    
    # Add Member
    add_member_event = {
        "pathParameters": {"comm_id": comm_id},
        "body": json.dumps({"user_id": "new_guest_123"})
    }
    add_resp = __import__('serverless.handlers.community').handlers.community.add_member_handler(add_member_event, None)
    assert add_resp["statusCode"] == 200
    
    # List Communities
    list_resp = __import__('serverless.handlers.community').handlers.community.list_communities_handler({}, None)
    assert list_resp["statusCode"] == 200
    comms = json.loads(list_resp["body"])
    assert any("new_guest_123" in c.get("members", []) for c in comms)
