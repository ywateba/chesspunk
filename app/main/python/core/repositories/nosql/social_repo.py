"""
Mongo Social Repository
=======================
Non-relational document mapping for Posts and Comments scaling out efficiently horizontally.
"""
from typing import List, Any
from core.repositories.base import SocialRepository
from core.db.documents import PostDocument, CommentDocument

class MongoSocialRepository(SocialRepository):
    async def create_post(self, community_id: Any, author_id: Any, content: str) -> Any:
        post = PostDocument(community_id=str(community_id), author_id=str(author_id), content=content)
        await post.insert()
        return post

    async def get_posts(self, community_id: Any, skip: int = 0, limit: int = 50) -> List[Any]:
        return await PostDocument.find(PostDocument.community_id == str(community_id)).skip(skip).limit(limit).to_list()

    async def create_comment(self, entity_type: str, entity_id: Any, author_id: Any, content: str) -> Any:
        comment = CommentDocument(
            entity_type=entity_type, entity_id=str(entity_id), author_id=str(author_id), content=content
        )
        await comment.insert()
        return comment

    async def get_comments(self, entity_type: str, entity_id: Any, skip: int = 0, limit: int = 50) -> List[Any]:
        return await CommentDocument.find(
            CommentDocument.entity_type == entity_type, 
            CommentDocument.entity_id == str(entity_id)
        ).skip(skip).limit(limit).to_list()
