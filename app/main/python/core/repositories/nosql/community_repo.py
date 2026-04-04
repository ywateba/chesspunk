"""
Mongo Community Repository
==========================
Persists embedded ODM arrays utilizing Beanie inherently bypassing explicit relationship structures securely.
"""

from typing import List, Optional, Any
from core.repositories.base import CommunityRepository
from core.schemas import schemas
from core.db.documents import CommunityDocument, CommunityMember

class MongoCommunityRepository(CommunityRepository):
    async def create_community(self, comm: schemas.CommunityCreate, owner_id: str) -> Any:
        db_comm = CommunityDocument(**comm.model_dump(), owner_id=owner_id)
        await db_comm.insert()
        return await self.join_community(str(db_comm.id), owner_id, role="owner")

    async def get_community(self, community_id: str) -> Optional[Any]:
        return await CommunityDocument.get(str(community_id))

    async def get_communities(self, skip: int = 0, limit: int = 100) -> List[Any]:
        return await CommunityDocument.find().skip(skip).limit(limit).to_list()

    async def join_community(self, community_id: str, user_id: str, role: str = "member") -> Any:
        comm = await self.get_community(community_id)
        if comm:
            if not any(m.user_id == user_id for m in comm.members):
                comm.members.append(CommunityMember(user_id=user_id, role=role))
                await comm.save()
        return comm

    async def get_members(self, community_id: str) -> List[Any]:
        comm = await self.get_community(community_id)
        return comm.members if comm else []
