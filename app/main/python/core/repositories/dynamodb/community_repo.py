import random
from typing import List, Optional, Any
from boto3.dynamodb.conditions import Attr
from core.schemas import schemas
from core.repositories.base import CommunityRepository
from core.repositories.dynamodb.base import get_resource, DynamoItem

class DynamoCommunityRepository(CommunityRepository):
    async def create_community(self, comm: schemas.CommunityCreate, owner_id: str) -> Any:
        comm_id = str(random.randint(100000, 9999999))
        async with get_resource() as resource:
            table = await resource.Table('Communities')
            item = {
                'id': comm_id,
                'name': comm.name,
                'description': comm.description,
                'owner_id': str(owner_id),
                'members': [{'user_id': str(owner_id), 'role': 'owner', 'rank': 1}]
            }
            await table.put_item(Item=item)
            return DynamoItem(**item)

    async def get_community(self, community_id: str) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Communities')
            resp = await table.get_item(Key={'id': str(community_id)})
            item = resp.get('Item')
            return DynamoItem(**item) if item else None

    async def get_communities(self, skip: int = 0, limit: int = 100) -> List[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Communities')
            resp = await table.scan()
            items = resp.get('Items', [])
            return [DynamoItem(**i) for i in items[skip:skip+limit]]
            
    async def join_community(self, community_id: str, user_id: str, role: str = "member") -> Any:
        comm = await self.get_community(community_id)
        if not comm:
            return None
        members = getattr(comm, 'members', [])
        if not any(str(m.get('user_id')) == str(user_id) for m in members):
            members.append({'user_id': str(user_id), 'role': role, 'rank': 0})
            async with get_resource() as resource:
                table = await resource.Table('Communities')
                await table.update_item(
                    Key={'id': str(community_id)},
                    UpdateExpression="set members = :m",
                    ExpressionAttributeValues={':m': members}
                )
        return await self.get_community(community_id)

    async def get_members(self, community_id: str) -> List[Any]:
        comm = await self.get_community(community_id)
        return getattr(comm, 'members', []) if comm else []
