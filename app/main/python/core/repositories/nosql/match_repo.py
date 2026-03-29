from typing import List, Optional, Any
from core.repositories.base import MatchRepository
from core.db.documents import MatchDocument

class MongoMatchRepository(MatchRepository):
    async def get_match(self, match_id: str) -> Optional[MatchDocument]:
        return await MatchDocument.get(match_id)

    async def create_matches(self, matches: List[Any]) -> List[MatchDocument]:
        # Translating legacy domain objects directly to MongoDB objects natively 
        docs = []
        for m in matches:
            doc = MatchDocument(
                competition_id=str(m.competition_id),
                white_player_id=str(m.white_player_id),
                black_player_id=str(m.black_player_id),
                result=m.result
            )
            await doc.insert()
            docs.append(doc)
        return docs

    async def update_match(self, db_match: Any, result: str, pgn_blueprint: str = None) -> MatchDocument:
        db_match.result = result
        if pgn_blueprint:
            db_match.pgn_blueprint = pgn_blueprint
        await db_match.save()
        return db_match
