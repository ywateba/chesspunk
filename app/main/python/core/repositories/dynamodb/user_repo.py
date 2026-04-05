import uuid
from typing import List, Optional, Any
from boto3.dynamodb.conditions import Attr
from core.repositories.base import UserRepository
from core.schemas import schemas
from core.repositories.dynamodb.base import get_resource, DynamoItem

class DynamoUserRepository(UserRepository):
    async def get_user(self, user_id: str) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Users')
            resp = await table.get_item(Key={'id': str(user_id)})
            item = resp.get('Item')
            return DynamoItem(**item) if item else None

    async def get_user_by_email(self, email: str) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Users')
            resp = await table.scan(FilterExpression=Attr('email').eq(email))
            items = resp.get('Items', [])
            return DynamoItem(**items[0]) if items else None

    async def get_user_by_username(self, username: str) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Users')
            resp = await table.scan(FilterExpression=Attr('username').eq(username))
            items = resp.get('Items', [])
            return DynamoItem(**items[0]) if items else None

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[Any]:
        # Note: True pagination with Limit & skip is complex in Dynamo without ExclusiveStartKey.
        async with get_resource() as resource:
            table = await resource.Table('Users')
            resp = await table.scan()
            items = resp.get('Items', [])
            return [DynamoItem(**item) for item in items[skip:skip+limit]]

    async def create_user(self, user: schemas.UserCreate, hashed_password: str) -> Any:
        # Pydantic schema expects int natively but Dynamo handles string keys.
        # Fallback to random integer ID for Dynamo to fulfill FastAPI schema bounds seamlessly.
        import random
        user_id = str(random.randint(100000, 9999999))
        
        async with get_resource() as resource:
            table = await resource.Table('Users')
            item = {
                'id': user_id,
                'email': user.email,
                'username': user.username,
                'hashed_password': hashed_password,
                'role': user.role,
                'elo': user.elo
            }
            await table.put_item(Item=item)
            return DynamoItem(**item)

    async def update_user_elo(self, user_id: str, new_elo: int) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Users')
            resp = await table.update_item(
                Key={'id': str(user_id)},
                UpdateExpression="set elo = :e",
                ExpressionAttributeValues={':e': new_elo},
                ReturnValues="ALL_NEW"
            )
            item = resp.get('Attributes')
            return DynamoItem(**item) if item else None
