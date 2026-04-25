import json
from serverless.handlers.social import create_post_handler, get_post_handler

def test_create_and_get_post():
    create_event = {
        "body": json.dumps({
            "content": "Hello World!",
            "author_id": "user123"
        })
    }
    
    response = create_post_handler(create_event, None)
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert body["content"] == "Hello World!"
    
    post_id = body["id"]
    
    get_event = {
        "pathParameters": {"post_id": post_id}
    }
    get_response = get_post_handler(get_event, None)
    assert get_response["statusCode"] == 200
    
    get_body = json.loads(get_response["body"])
    assert get_body["id"] == post_id
    
    # Create Comment
    comment_event = {
        "pathParameters": {"post_id": post_id},
        "body": json.dumps({"content": "Nice post!", "author_id": "commenter22"})
    }
    comment_resp = __import__('serverless.handlers.social').handlers.social.create_comment_handler(comment_event, None)
    assert comment_resp["statusCode"] == 200
    
    # List Posts
    list_resp = __import__('serverless.handlers.social').handlers.social.list_posts_handler({}, None)
    assert list_resp["statusCode"] == 200
    posts = json.loads(list_resp["body"])
    assert "comments" in posts[0]
    assert posts[0]["comments"][0]["content"] == "Nice post!"
