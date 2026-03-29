from typing import List, Optional
from core.repositories.base import UserRepository
from core.schemas import schemas
from core.db.documents import UserDocument
from bson import ObjectId

class MongoUserRepository(UserRepository):
    async def get_user(self, user_id: str) -> Optional[UserDocument]:
        return await UserDocument.get(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UserDocument]:
        return await UserDocument.find_one(UserDocument.email == email)

    async def get_user_by_username(self, username: str) -> Optional[UserDocument]:
        return await UserDocument.find_one(UserDocument.username == username)

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserDocument]:
        return await UserDocument.find_all().skip(skip).limit(limit).to_list()

    async def create_user(self, user: schemas.UserCreate, hashed_password: str) -> UserDocument:
        user_doc = UserDocument(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        await user_doc.insert()
        return user_doc
