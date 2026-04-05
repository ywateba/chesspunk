import pytest
from core.repositories.dynamodb.social_repo import DynamoSocialRepository

@pytest.mark.asyncio
async def test_dynamo_social_repo_full_coverage():
    repo = DynamoSocialRepository()
    
    # 1. create_post
    post = await repo.create_post("comm-1", "author-1", "Test Post Content")
    assert post is not None
    assert getattr(post, 'entity_type') == "post"
    assert getattr(post, 'content') == "Test Post Content"

    # 2. get_posts
    posts = await repo.get_posts("comm-1")
    assert len(posts) >= 1
    assert any(str(p.id) == str(post.id) for p in posts)
    
    # Empty post
    assert len(await repo.get_posts("comm-invalid")) == 0

    # 3. create_comment
    comment = await repo.create_comment("post", str(post.id), "author-2", "Test Comment")
    assert comment is not None
    assert getattr(comment, 'type') == 'comment'
    assert getattr(comment, 'content') == "Test Comment"

    # 4. get_comments
    comments = await repo.get_comments("post", str(post.id))
    assert len(comments) >= 1
    assert any(str(c.id) == str(comment.id) for c in comments)
    
    # Empty comments
    assert len(await repo.get_comments("invalid", "999")) == 0
