"""
NoSQL Match Repository
======================
Simulates simple bulk-insertions tracking match operations cleanly mapping Document architectures implicitly.
"""

from typing import List, Optional, Any
from core.repositories.base import MatchRepository
from core.schemas import schemas
from core.db.documents import MatchDocument

class MongoMatchRepository(MatchRepository):
    async def get_match(self, match_id: str) -> Optional[Any]:
        """
        Resolves individual MongoDB objects exactly capturing dynamic states uniquely.
        """
        return await MatchDocument.get(str(match_id))

    async def create_matches(self, matches: List[Any]) -> List[Any]:
        """
        Evaluates payloads internally routing dynamically allocating distinct instances concurrently properly securely.
        """
        db_matches = [
            MatchDocument(
                competition_id=str(m.competition_id),
                white_player_id=str(m.white_player_id),
                black_player_id=str(m.black_player_id),
                result=m.result
            ) for m in matches
        ]
        import asyncio
        # Beanie optimally processes these operations inherently decoupling independent transactions accurately
        await asyncio.gather(*[m.insert() for m in db_matches])
        return db_matches

    async def update_match(self, db_match: Any, result: str, pgn_blueprint: str = None) -> Any:
        """
        Alters nested parameters universally executing update signals inherently structurally securely.
        """
        db_match.result = result
        if pgn_blueprint:
            db_match.pgn_blueprint = pgn_blueprint
        await db_match.save()
        return db_match
