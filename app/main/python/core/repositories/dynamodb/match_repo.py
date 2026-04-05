import random
from typing import List, Optional, Any
from boto3.dynamodb.conditions import Attr
from core.repositories.base import MatchRepository
from core.repositories.dynamodb.base import get_resource, DynamoItem

class DynamoMatchRepository(MatchRepository):
    async def get_match(self, match_id: str) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Matches')
            resp = await table.get_item(Key={'id': str(match_id)})
            item = resp.get('Item')
            return DynamoItem(**item) if item else None

    async def create_matches(self, matches: List[Any]) -> List[Any]:
        created_matches = []
        async with get_resource() as resource:
            table = await resource.Table('Matches')
            for match in matches:
                match_id = str(random.randint(100000, 9999999))
                item = {
                    'id': match_id,
                    'competition_id': str(getattr(match, 'competition_id', None)),
                    'white_player_id': str(getattr(match, 'white_player_id', None)),
                    'black_player_id': str(getattr(match, 'black_player_id', None)),
                    'result': getattr(match, 'result', '*')
                }
                await table.put_item(Item=item)
                created_matches.append(DynamoItem(**item))
        return created_matches

    async def update_match(self, db_match: Any, result: str, pgn_blueprint: str = None) -> Any:
        async with get_resource() as resource:
            table = await resource.Table('Matches')
            
            expr = "set #res = :r"
            vals = {':r': result}
            names = {'#res': 'result'}
            
            if pgn_blueprint is not None:
                expr += ", pgn_blueprint = :p"
                vals[':p'] = pgn_blueprint

            resp = await table.update_item(
                Key={'id': str(db_match.id)},
                UpdateExpression=expr,
                ExpressionAttributeValues=vals,
                ExpressionAttributeNames=names,
                ReturnValues="ALL_NEW"
            )
            item = resp.get('Attributes')
            return DynamoItem(**item) if item else None
