import os
from unittest.mock import patch
from serverless.handlers import community

@patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1"})
def test_create_and_get_community():
    
    # 1. Create Community
    comm = community.create_community({
        "name": "Chess Masters",
        "owner_id": "user123"
    })
    assert comm["name"] == "Chess Masters"
    comm_id = comm["id"]
    
    # 2. Get Community
    get_comm = community.get_community(comm_id)
    assert get_comm["id"] == comm_id
    
    # 3. Add Member
    # Note: `add_member` uses `member_id` as per the implementation
    community.add_member(comm_id, {"member_id": "new_guest_123"})
    
    # 4. List Communities
    comms = community.list_communities()
    assert any("new_guest_123" in c.get("members", []) for c in comms)
