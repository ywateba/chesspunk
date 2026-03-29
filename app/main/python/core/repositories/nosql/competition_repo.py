"""
NoSQL Competition Repository
============================
Integrates complex relational structures cleanly simulating "joinedloads" locally by orchestrating
secondary Beanie asynchronous sweeps extracting matches explicitly matching ID filters precisely.
"""

from typing import List, Optional, Any
from core.repositories.base import CompetitionRepository
from core.schemas import schemas
from core.db.documents import CompetitionDocument, UserDocument, MatchDocument
from bson import ObjectId

class MongoCompetitionRepository(CompetitionRepository):
    async def get_competition(self, competition_id: str) -> Optional[Any]:
        """
        Reassembles tournament objects safely querying explicitly nested relationship arrays independently dynamically.
        This entirely replaces `selectinload` executing standard parallel $in array queries exclusively seamlessly.
        """
        comp = await CompetitionDocument.get(competition_id)
        if not comp: return None
        
        # Emulate the explicit SelectInLoad relation fetches mapped over dynamic properties dynamically safely.
        object_ids = [ObjectId(pid) for pid in comp.player_ids]
        comp.players = await UserDocument.find({"_id": {"$in": object_ids}}).to_list()
        comp.matches = await MatchDocument.find({"competition_id": str(comp.id)}).to_list()
        return comp

    async def get_competitions(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """
        Yields paginated objects structurally mapping base attributes safely matching SQL architectures directly natively.
        """
        comps = await CompetitionDocument.find().skip(skip).limit(limit).to_list()
        return comps

    async def create_competition(self, comp: schemas.CompetitionCreate) -> Any:
        """
        Insert standard root instances persistently instantly committing into the database configurations.
        """
        db_comp = CompetitionDocument(**comp.model_dump())
        return await db_comp.insert()

    async def add_player_to_competition(self, db_comp: Any, user: Any) -> Any:
        """
        Injects ID values inherently maintaining Array relationships securely over lists seamlessly bypassing complex Junction abstractions explicitly.
        """
        user_id_str = str(user.id)
        if user_id_str not in db_comp.player_ids:
            db_comp.player_ids.append(user_id_str)
            await db_comp.save()
        return await self.get_competition(str(db_comp.id))
        
    async def update_competition_status(self, db_comp: Any, status: str) -> Any:
        """
        Dynamically applies local modifications verifying updates universally.
        """
        db_comp.status = status
        await db_comp.save()
        return await self.get_competition(str(db_comp.id))
