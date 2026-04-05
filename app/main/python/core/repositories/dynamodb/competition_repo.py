import random
from typing import List, Optional, Any
from boto3.dynamodb.conditions import Attr
from core.schemas import schemas
from core.repositories.base import CompetitionRepository
from core.repositories.dynamodb.base import get_resource, DynamoItem

class DynamoCompetitionRepository(CompetitionRepository):
    async def get_competition(self, competition_id: str) -> Optional[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Competitions')
            resp = await table.get_item(Key={'id': str(competition_id)})
            item = resp.get('Item')
            if not item: return None
            
            comp = DynamoItem(**item)
            
            # Simple simulation of relational joinedload querying
            players_data = []
            if getattr(comp, 'players', []):
                users_tbl = await resource.Table('Users')
                for pid in comp.players:
                    u_resp = await users_tbl.get_item(Key={'id': str(pid)})
                    u_item = u_resp.get('Item')
                    if u_item:
                        # Ensures schema validation safely 
                        u_item['id'] = int(u_item['id']) if str(u_item['id']).isdigit() else u_item['id']
                        players_data.append(schemas.User(**u_item))
            comp.players = players_data
            
            matches_tbl = await resource.Table('Matches')
            m_resp = await matches_tbl.scan(FilterExpression=Attr('competition_id').eq(str(comp.id)))
            m_items = m_resp.get('Items', [])
            comp.matches = [schemas.Match(**m) for m in m_items]
            
            return comp

    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[Any]:
        async with get_resource() as resource:
            table = await resource.Table('Competitions')
            resp = await table.scan()
            items = resp.get('Items', [])
            
            comps = []
            for item in items[skip:skip+limit]:
                comp = DynamoItem(**item)
                
                players_data = []
                if getattr(comp, 'players', []):
                    users_tbl = await resource.Table('Users')
                    for pid in comp.players:
                        u_resp = await users_tbl.get_item(Key={'id': str(pid)})
                        u_item = u_resp.get('Item')
                        if u_item:
                            u_item['id'] = int(u_item['id']) if str(u_item['id']).isdigit() else u_item['id']
                            players_data.append(schemas.User(**u_item))
                comp.players = players_data
                
                matches_tbl = await resource.Table('Matches')
                m_resp = await matches_tbl.scan(FilterExpression=Attr('competition_id').eq(str(comp.id)))
                m_items = m_resp.get('Items', [])
                comp.matches = [schemas.Match(**m) for m in m_items]
                
                comps.append(comp)
            return comps

    async def create_competition(self, comp: schemas.CompetitionCreate) -> Any:
        comp_id = str(random.randint(100000, 9999999))
        async with get_resource() as resource:
            table = await resource.Table('Competitions')
            item = {
                'id': comp_id,
                'name': comp.name,
                'format': comp.format,
                'community_id': str(comp.community_id) if comp.community_id else None,
                'status': 'open',
                'players': []
            }
            await table.put_item(Item=item)
            return await self.get_competition(str(item['id']))

    async def add_player_to_competition(self, db_comp: Any, user: Any) -> Any:
        user_id_str = str(user.id)
        current_players = getattr(db_comp, 'players', [])
        player_ids = [str(p.id) if hasattr(p, 'id') else str(p) for p in current_players]
        
        if user_id_str not in player_ids:
            player_ids.append(user_id_str)
            async with get_resource() as resource:
                table = await resource.Table('Competitions')
                await table.update_item(
                    Key={'id': str(db_comp.id)},
                    UpdateExpression="set players = :p",
                    ExpressionAttributeValues={':p': player_ids}
                )
        return await self.get_competition(db_comp.id)

    async def update_competition_status(self, db_comp: Any, status: str) -> Any:
        async with get_resource() as resource:
            table = await resource.Table('Competitions')
            await table.update_item(
                Key={'id': str(db_comp.id)},
                UpdateExpression="set #st = :s",
                ExpressionAttributeValues={':s': status},
                ExpressionAttributeNames={'#st': 'status'}
            )
        return await self.get_competition(db_comp.id)
