import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_community_lifecycle(test_client: AsyncClient):
    # 1. Signup users
    await test_client.post("/auth/signup", json={"username": "founder", "email": "founder@test.com", "password": "pass"})
    await test_client.post("/auth/signup", json={"username": "member1", "email": "m1@test.com", "password": "pass"})
    
    # 2. Get tokens
    t_owner = (await test_client.post("/auth/login", data={"username": "founder", "password": "pass"})).json()["access_token"]
    t_member = (await test_client.post("/auth/login", data={"username": "member1", "password": "pass"})).json()["access_token"]
    
    # 3. Create Community
    res = await test_client.post("/communities/", json={"name": "Chess Masters", "description": "Elite club"}, headers={"Authorization": f"Bearer {t_owner}"})
    assert res.status_code == 200
    comm_id = res.json()["id"]
    
    # 4. Join Community
    res = await test_client.post(f"/communities/{comm_id}/join", headers={"Authorization": f"Bearer {t_member}"})
    assert res.status_code == 200
    
    # 5. Create Post
    res = await test_client.post(f"/communities/{comm_id}/posts", json={"content": "Hello World!"}, headers={"Authorization": f"Bearer {t_owner}"})
    assert res.status_code == 200
    post_id = res.json()["id"]
    
    # 6. Comment on Post
    res = await test_client.post(f"/communities/posts/{post_id}/comments", json={"content": "Nice post"}, headers={"Authorization": f"Bearer {t_member}"})
    assert res.status_code == 200
    
    # 7. Verify List
    res = await test_client.get(f"/communities/{comm_id}/posts")
    assert len(res.json()) == 1
    assert res.json()[0]["content"] == "Hello World!"
