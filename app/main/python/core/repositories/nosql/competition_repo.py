from typing import List, Optional, Any
from core.repositories.base import CompetitionRepository
from core.schemas import schemas
from core.db.documents import CompetitionDocument, UserDocument, MatchDocument
from bson import ObjectId

class MongoCompetitionRepository(CompetitionRepository):
    async def get_competition(self, competition_id: str) -> Optional[Any]:
        comp = await CompetitionDocument.get(competition_id)
        if not comp: return None
        
        # Emulate the explicit SelectInLoad relation fetches from SQLAlchemy for Services natively
        object_ids = [ObjectId(pid) for pid in comp.player_ids]
        comp.players = await UserDocument.find({"_id": {"$in": object_ids}}).to_list()
        comp.matches = await MatchDocument.find({"competition_id": str(comp.id)}).to_list()
        return comp

    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[CompetitionDocument]:
        return await CompetitionDocument.find_all().skip(skip).limit(limit).to_list()

    async def create_competition(self, comp: schemas.CompetitionCreate) -> CompetitionDocument:
        comp_doc = CompetitionDocument(name=comp.name)
        await comp_doc.insert()
        return await self.get_competition(str(comp_doc.id))

    async def add_player_to_competition(self, db_comp: Any, user: Any) -> CompetitionDocument:
        user_id_str = str(user.id)
        if user_id_str not in db_comp.player_ids:
            db_comp.player_ids.append(user_id_str)
            await db_comp.save()
        return await self.get_competition(str(db_comp.id))

    async def update_competition_status(self, db_comp: Any, status: str) -> CompetitionDocument:
        db_comp.status = status
        await db_comp.save()
        return await self.get_competition(str(db_comp.id))
