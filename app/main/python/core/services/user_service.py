from core.repositories.base import UserRepository

async def get_users_list(user_repo: UserRepository, skip: int = 0, limit: int = 100):
    return await user_repo.get_users(skip=skip, limit=limit)
