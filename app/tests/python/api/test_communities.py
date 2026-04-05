"""
Tests for Communities API Endpoints
====================================
Tests all endpoints in routers/communities.py that account for the database engine in use.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_community_authorized(test_client: AsyncClient):
    """Test creating a community with proper authorization."""
    # Create and login a user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "creator", "email": "creator@test.com", "password": "password"}
    )
    assert signup_response.status_code == 200

    login_response = await test_client.post(
        "/auth/login",
        data={"username": "creator", "password": "password"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create community
    response = await test_client.post(
        "/communities/",
        json={"name": "Test Community", "description": "A test community"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Community"
    assert data["description"] == "A test community"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_community_unauthorized(test_client: AsyncClient):
    """Test creating a community without authentication."""
    response = await test_client.post(
        "/communities/",
        json={"name": "Unauthorized Community", "description": "Should fail"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_communities(test_client: AsyncClient):
    """Test getting the list of communities."""
    response = await test_client.get("/communities/")
    assert response.status_code == 200
    communities = response.json()
    assert isinstance(communities, list)


@pytest.mark.asyncio
async def test_get_community_not_found(test_client: AsyncClient):
    """Test getting a non-existent community."""
    response = await test_client.get("/communities/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_join_community_authorized(test_client: AsyncClient):
    """Test joining a community with proper authorization."""
    # Create users
    await test_client.post("/auth/signup", json={"username": "owner", "email": "owner@test.com", "password": "password"})
    await test_client.post("/auth/signup", json={"username": "joiner", "email": "joiner@test.com", "password": "password"})

    # Login users
    owner_login = await test_client.post("/auth/login", data={"username": "owner", "password": "password"})
    joiner_login = await test_client.post("/auth/login", data={"username": "joiner", "password": "password"})
    owner_token = owner_login.json()["access_token"]
    joiner_token = joiner_login.json()["access_token"]

    # Create community
    create_response = await test_client.post(
        "/communities/",
        json={"name": "Join Test Community", "description": "Test for joining"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert create_response.status_code == 200
    comm_id = create_response.json()["id"]

    # Join community
    response = await test_client.post(
        f"/communities/{comm_id}/join",
        headers={"Authorization": f"Bearer {joiner_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_join_community_unauthorized(test_client: AsyncClient):
    """Test joining a community without authentication."""
    response = await test_client.post("/communities/1/join")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_join_community_not_found(test_client: AsyncClient):
    """Test joining a non-existent community."""
    # Create user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "joiner2", "email": "joiner2@test.com", "password": "password"}
    )
    assert signup_response.status_code == 200

    login_response = await test_client.post(
        "/auth/login",
        data={"username": "joiner2", "password": "password"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = await test_client.post(
        "/communities/999/join",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_post_authorized(test_client: AsyncClient):
    """Test creating a post in a community."""
    # Create user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "poster", "email": "poster@test.com", "password": "password"}
    )
    assert signup_response.status_code == 200

    login_response = await test_client.post(
        "/auth/login",
        data={"username": "poster", "password": "password"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create community
    create_comm_response = await test_client.post(
        "/communities/",
        json={"name": "Post Test Community", "description": "Test for posting"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_comm_response.status_code == 200
    comm_id = create_comm_response.json()["id"]

    # Create post
    response = await test_client.post(
        f"/communities/{comm_id}/posts",
        json={"content": "This is a test post"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a test post"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_post_unauthorized(test_client: AsyncClient):
    """Test creating a post without authentication."""
    response = await test_client.post(
        "/communities/1/posts",
        json={"content": "Unauthorized post"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_posts(test_client: AsyncClient):
    """Test getting posts from a community."""
    # Create user
    signup_response = await test_client.post(
        "/auth/signup",
        json={"username": "getter", "email": "getter@test.com", "password": "password"}
    )
    assert signup_response.status_code == 200

    login_response = await test_client.post(
        "/auth/login",
        data={"username": "getter", "password": "password"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create community
    create_comm_response = await test_client.post(
        "/communities/",
        json={"name": "Get Posts Test Community", "description": "Test for getting posts"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_comm_response.status_code == 200
    comm_id = create_comm_response.json()["id"]

    # Create post
    create_post_response = await test_client.post(
        f"/communities/{comm_id}/posts",
        json={"content": "Test post content"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_post_response.status_code == 200

    response = await test_client.get(f"/communities/{comm_id}/posts")
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) >= 1
    assert posts[0]["content"] == "Test post content"


@pytest.mark.asyncio
async def test_create_comment_authorized(test_client: AsyncClient):
    """Test creating a comment on a post."""
    # Create users
    await test_client.post("/auth/signup", json={"username": "commenter", "email": "commenter@test.com", "password": "password"})
    await test_client.post("/auth/signup", json={"username": "commenter2", "email": "commenter2@test.com", "password": "password"})

    # Login users
    commenter_login = await test_client.post("/auth/login", data={"username": "commenter", "password": "password"})
    commenter2_login = await test_client.post("/auth/login", data={"username": "commenter2", "password": "password"})
    commenter_token = commenter_login.json()["access_token"]
    commenter2_token = commenter2_login.json()["access_token"]

    # Create community
    create_comm_response = await test_client.post(
        "/communities/",
        json={"name": "Comment Test Community", "description": "Test for commenting"},
        headers={"Authorization": f"Bearer {commenter_token}"}
    )
    assert create_comm_response.status_code == 200
    comm_id = create_comm_response.json()["id"]

    # Create post
    create_post_response = await test_client.post(
        f"/communities/{comm_id}/posts",
        json={"content": "Post to comment on"},
        headers={"Authorization": f"Bearer {commenter_token}"}
    )
    assert create_post_response.status_code == 200
    post_id = create_post_response.json()["id"]

    # Create comment
    response = await test_client.post(
        f"/communities/posts/{post_id}/comments",
        json={"content": "This is a comment"},
        headers={"Authorization": f"Bearer {commenter2_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a comment"


@pytest.mark.asyncio
async def test_create_comment_unauthorized(test_client: AsyncClient):
    """Test creating a comment without authentication."""
    response = await test_client.post(
        "/communities/posts/1/comments",
        json={"content": "Unauthorized comment"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_comments(test_client: AsyncClient):
    """Test getting comments for a post."""
    # Create users
    await test_client.post("/auth/signup", json={"username": "comment_getter", "email": "comment_getter@test.com", "password": "password"})
    await test_client.post("/auth/signup", json={"username": "comment_poster", "email": "comment_poster@test.com", "password": "password"})

    # Login users
    getter_login = await test_client.post("/auth/login", data={"username": "comment_getter", "password": "password"})
    poster_login = await test_client.post("/auth/login", data={"username": "comment_poster", "password": "password"})
    getter_token = getter_login.json()["access_token"]
    poster_token = poster_login.json()["access_token"]

    # Create community
    create_comm_response = await test_client.post(
        "/communities/",
        json={"name": "Get Comments Test Community", "description": "Test for getting comments"},
        headers={"Authorization": f"Bearer {getter_token}"}
    )
    assert create_comm_response.status_code == 200
    comm_id = create_comm_response.json()["id"]

    # Create post
    create_post_response = await test_client.post(
        f"/communities/{comm_id}/posts",
        json={"content": "Post for comments"},
        headers={"Authorization": f"Bearer {getter_token}"}
    )
    assert create_post_response.status_code == 200
    post_id = create_post_response.json()["id"]

    # Create comment
    create_comment_response = await test_client.post(
        f"/communities/posts/{post_id}/comments",
        json={"content": "Test comment"},
        headers={"Authorization": f"Bearer {poster_token}"}
    )
    assert create_comment_response.status_code == 200

    response = await test_client.get(f"/communities/posts/{post_id}/comments")
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) >= 1
    assert comments[0]["content"] == "Test comment"


# Note: These tests focus on API endpoint structure, authentication, and basic functionality.
# More comprehensive integration tests could cover full community lifecycles, permissions, and edge cases.
