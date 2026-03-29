from sqlalchemy.ext.asyncio import AsyncSession
from core.db.crud import users as users_crud

async def get_users_list(db: AsyncSession, skip: int = 0, limit: int = 100):
    return await users_crud.get_users(db, skip=skip, limit=limit)
