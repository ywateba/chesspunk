import os
from unittest.mock import patch
from serverless.handlers import social

@patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1"})
def test_create_and_get_post():
    
    # 1. Create Post
    post = social.create_post({
        "content": "Hello World!",
        "author_id": "user123"
    })
    assert post["content"] == "Hello World!"
    post_id = post["id"]
    
    # 2. Get Post
    get_post = social.get_post(post_id)
    assert get_post["id"] == post_id
    
    # 3. Create Comment
    social.create_comment(post_id, {"content": "Nice post!", "author_id": "commenter22"})
    
    # 4. List Posts
    posts = social.list_posts()
    assert "comments" in posts[0]
    assert posts[0]["comments"][0]["content"] == "Nice post!"
