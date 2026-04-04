"""
NoSQL User Repository
=====================
Satisfies the identical abstraction protocols tracking natively onto Beanie ODM collections independently.
"""

from typing import List, Optional, Any
from core.repositories.base import UserRepository
from core.schemas import schemas
from core.db.documents import UserDocument

class MongoUserRepository(UserRepository):
    async def get_user(self, user_id: str) -> Optional[Any]:
        """
        Bypasses integers natively mapping exact string UUID queries safely across MongoDB schemas.
        """
        return await UserDocument.get(str(user_id))

    async def get_user_by_email(self, email: str) -> Optional[Any]:
        """
        Locate single instances checking embedded email keys explicitly relying on asynchronous ODM wrappers.
        """
        return await UserDocument.find_one(UserDocument.email == email)

    async def get_user_by_username(self, username: str) -> Optional[Any]:
        """
        Ensures structural indexing operates correctly across arbitrary username comparisons explicitly.
        """
        return await UserDocument.find_one(UserDocument.username == username)

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """
        Scans all Beanie collection entries returning pure lists automatically bypassing cursor loops.
        """
        return await UserDocument.find().skip(skip).limit(limit).to_list()

    async def create_user(self, user: schemas.UserCreate, hashed_password: str) -> Any:
        """
        Allocates exact Document abstractions structurally injecting natively persisting arrays dynamically directly.
        """
        db_user = UserDocument(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        return await db_user.insert()

    async def update_user_elo(self, user_id: str, new_elo: int) -> Optional[Any]:
        """
        Directly saves delta points safely maintaining embedded structure validations.
        """
        user = await self.get_user(user_id)
        if user:
            user.elo = new_elo
            await user.save()
        return user
