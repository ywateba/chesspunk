import random
from typing import List, Optional, Any
from boto3.dynamodb.conditions import Attr
from core.repositories.base import SocialRepository
from core.repositories.dynamodb.base import get_resource, DynamoItem

class DynamoSocialRepository(SocialRepository):
    async def create_post(self, community_id: str, author_id: str, content: str) -> Any:
        post_id = str(random.randint(100000, 9999999))
        async with get_resource() as resource:
            table = await resource.Table('Social')
            item = {
                'id': post_id,
                'entity_type': 'post',
                'community_id': str(community_id),
                'author_id': str(author_id),
                'content': content
            }
            await table.put_item(Item=item)
            return DynamoItem(**item)

    async def get_posts(self, community_id: str, skip: int = 0, limit: int = 50) -> List[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Social')
            resp = await table.scan(
                FilterExpression=Attr('entity_type').eq('post') & Attr('community_id').eq(str(community_id))
            )
            items = resp.get('Items', [])
            return [DynamoItem(**i) for i in items[skip:skip+limit]]
            
    async def create_comment(self, entity_type: str, entity_id: str, author_id: str, content: str) -> Any:
        comment_id = str(random.randint(100000, 9999999))
        async with get_resource() as resource:
            table = await resource.Table('Social')
            item = {
                'id': comment_id,
                'type': 'comment', # Safe internal type
                'entity_type': entity_type,
                'entity_id': str(entity_id),
                'author_id': str(author_id),
                'content': content
            }
            await table.put_item(Item=item)
            return DynamoItem(**item)

    async def get_comments(self, entity_type: str, entity_id: str, skip: int = 0, limit: int = 50) -> List[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Social')
            resp = await table.scan(
                FilterExpression=Attr('type').eq('comment') & Attr('entity_type').eq(entity_type) & Attr('entity_id').eq(str(entity_id))
            )
            items = resp.get('Items', [])
            return [DynamoItem(**i) for i in items[skip:skip+limit]]
