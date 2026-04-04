"""
Tests for SQL Social Repository
===============================
Tests all functions in core.repositories.sql.social_repo that interact with the SQL database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.sql.social_repo import SQLSocialRepository
from core.repositories.sql.community_repo import SQLCommunityRepository
from core.repositories.sql.user_repo import SQLUserRepository
from core.repositories.sql.competition_repo import SQLCompetitionRepository
from core.repositories.sql.match_repo import SQLMatchRepository
from core.schemas import schemas
from core.db import models


@pytest.mark.asyncio
async def test_create_post(db_session: AsyncSession):
    """Test creating a post in a community."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and user
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, owner.id)

    # Create post
    post = await social_repo.create_post(community.id, owner.id, "Hello, this is a test post!")

    assert post.id is not None
    assert post.community_id == community.id
    assert post.author_id == owner.id
    assert post.content == "Hello, this is a test post!"


@pytest.mark.asyncio
async def test_get_posts(db_session: AsyncSession):
    """Test getting posts from a community."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and user
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, owner.id)

    # Create multiple posts
    post_contents = ["Post 1", "Post 2", "Post 3"]
    for content in post_contents:
        await social_repo.create_post(community.id, owner.id, content)

    # Get posts
    posts = await social_repo.get_posts(community.id)

    assert len(posts) == 3
    contents = [post.content for post in posts]
    assert "Post 1" in contents
    assert "Post 2" in contents
    assert "Post 3" in contents

    # All posts should be from the same author and community
    for post in posts:
        assert post.community_id == community.id
        assert post.author_id == owner.id


@pytest.mark.asyncio
async def test_get_posts_pagination(db_session: AsyncSession):
    """Test posts pagination."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and user
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, owner.id)

    # Create 5 posts
    for i in range(5):
        await social_repo.create_post(community.id, owner.id, f"Post {i}")

    # Get first 2 posts
    posts = await social_repo.get_posts(community.id, skip=0, limit=2)
    assert len(posts) == 2

    # Get next 2 posts
    posts = await social_repo.get_posts(community.id, skip=2, limit=2)
    assert len(posts) == 2


@pytest.mark.asyncio
async def test_get_posts_different_communities(db_session: AsyncSession):
    """Test that posts are isolated to their communities."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create two communities and users
    owner1_data = schemas.UserCreate(username="owner1", email="owner1@example.com", password="password")
    owner2_data = schemas.UserCreate(username="owner2", email="owner2@example.com", password="password")
    owner1 = await user_repo.create_user(owner1_data, "hashed")
    owner2 = await user_repo.create_user(owner2_data, "hashed")

    comm1_data = schemas.CommunityCreate(name="Community 1")
    comm2_data = schemas.CommunityCreate(name="Community 2")
    community1 = await community_repo.create_community(comm1_data, owner1.id)
    community2 = await community_repo.create_community(comm2_data, owner2.id)

    # Create posts in each community
    await social_repo.create_post(community1.id, owner1.id, "Post in community 1")
    await social_repo.create_post(community2.id, owner2.id, "Post in community 2")

    # Get posts from each community
    posts1 = await social_repo.get_posts(community1.id)
    posts2 = await social_repo.get_posts(community2.id)

    assert len(posts1) == 1
    assert len(posts2) == 1
    assert posts1[0].content == "Post in community 1"
    assert posts2[0].content == "Post in community 2"


@pytest.mark.asyncio
async def test_create_comment_on_post(db_session: AsyncSession):
    """Test creating a comment on a post."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and users
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    commenter_data = schemas.UserCreate(username="commenter", email="commenter@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")
    commenter = await user_repo.create_user(commenter_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, owner.id)

    # Create post
    post = await social_repo.create_post(community.id, owner.id, "Test post")

    # Create comment on post
    comment = await social_repo.create_comment("post", post.id, commenter.id, "Great post!")

    assert comment.id is not None
    assert comment.entity_type == "post"
    assert comment.entity_id == post.id
    assert comment.author_id == commenter.id
    assert comment.content == "Great post!"


@pytest.mark.asyncio
async def test_create_comment_on_match(db_session: AsyncSession):
    """Test creating a comment on a match."""
    social_repo = SQLSocialRepository(db_session)
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create prerequisite data
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)

    user_data1 = schemas.UserCreate(username="white", email="white@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="black", email="black@example.com", password="pass")
    commenter_data = schemas.UserCreate(username="commenter", email="commenter@example.com", password="pass")
    white_player = await user_repo.create_user(user_data1, "hashed")
    black_player = await user_repo.create_user(user_data2, "hashed")
    commenter = await user_repo.create_user(commenter_data, "hashed")

    # Create match
    match = models.Match(
        competition_id=comp.id,
        white_player_id=white_player.id,
        black_player_id=black_player.id
    )
    created_matches = await match_repo.create_matches([match])
    created_match = created_matches[0]

    # Create comment on match
    comment = await social_repo.create_comment("match", created_match.id, commenter.id, "Interesting game!")

    assert comment.id is not None
    assert comment.entity_type == "match"
    assert comment.entity_id == created_match.id
    assert comment.author_id == commenter.id
    assert comment.content == "Interesting game!"


@pytest.mark.asyncio
async def test_get_comments_on_post(db_session: AsyncSession):
    """Test getting comments for a post."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and users
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    commenter_data = schemas.UserCreate(username="commenter", email="commenter@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")
    commenter = await user_repo.create_user(commenter_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, owner.id)

    # Create post
    post = await social_repo.create_post(community.id, owner.id, "Test post")

    # Create multiple comments
    comment_contents = ["Comment 1", "Comment 2", "Comment 3"]
    for content in comment_contents:
        await social_repo.create_comment("post", post.id, commenter.id, content)

    # Get comments
    comments = await social_repo.get_comments("post", post.id)

    assert len(comments) == 3
    contents = [comment.content for comment in comments]
    assert "Comment 1" in contents
    assert "Comment 2" in contents
    assert "Comment 3" in contents

    # All comments should be on the same post
    for comment in comments:
        assert comment.entity_type == "post"
        assert comment.entity_id == post.id


@pytest.mark.asyncio
async def test_get_comments_pagination(db_session: AsyncSession):
    """Test comments pagination."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create community and users
    owner_data = schemas.UserCreate(username="owner", email="owner@example.com", password="password")
    commenter_data = schemas.UserCreate(username="commenter", email="commenter@example.com", password="password")
    owner = await user_repo.create_user(owner_data, "hashed")
    commenter = await user_repo.create_user(commenter_data, "hashed")

    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, owner.id)

    # Create post
    post = await social_repo.create_post(community.id, owner.id, "Test post")

    # Create 5 comments
    for i in range(5):
        await social_repo.create_comment("post", post.id, commenter.id, f"Comment {i}")

    # Get first 2 comments
    comments = await social_repo.get_comments("post", post.id, skip=0, limit=2)
    assert len(comments) == 2

    # Get next 2 comments
    comments = await social_repo.get_comments("post", post.id, skip=2, limit=2)
    assert len(comments) == 2


@pytest.mark.asyncio
async def test_get_comments_different_entities(db_session: AsyncSession):
    """Test that comments are isolated to their entities."""
    social_repo = SQLSocialRepository(db_session)
    community_repo = SQLCommunityRepository(db_session)
    match_repo = SQLMatchRepository(db_session)
    comp_repo = SQLCompetitionRepository(db_session)
    user_repo = SQLUserRepository(db_session)

    # Create users
    user_data1 = schemas.UserCreate(username="user1", email="user1@example.com", password="pass")
    user_data2 = schemas.UserCreate(username="user2", email="user2@example.com", password="pass")
    user1 = await user_repo.create_user(user_data1, "hashed")
    user2 = await user_repo.create_user(user_data2, "hashed")

    # Create community and post
    comm_data = schemas.CommunityCreate(name="Test Community")
    community = await community_repo.create_community(comm_data, user1.id)
    post = await social_repo.create_post(community.id, user1.id, "Test post")

    # Create match
    comp_data = schemas.CompetitionCreate(name="Test Tournament")
    comp = await comp_repo.create_competition(comp_data)
    match = models.Match(competition_id=comp.id, white_player_id=user1.id, black_player_id=user2.id)
    created_matches = await match_repo.create_matches([match])
    created_match = created_matches[0]

    # Create comments on both entities
    await social_repo.create_comment("post", post.id, user2.id, "Comment on post")
    await social_repo.create_comment("match", created_match.id, user2.id, "Comment on match")

    # Get comments for each entity
    post_comments = await social_repo.get_comments("post", post.id)
    match_comments = await social_repo.get_comments("match", created_match.id)

    assert len(post_comments) == 1
    assert len(match_comments) == 1
    assert post_comments[0].content == "Comment on post"
    assert match_comments[0].content == "Comment on match"