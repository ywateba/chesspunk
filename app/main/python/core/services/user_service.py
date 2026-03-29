"""
User Service
============
Abstract logic mappings extracting pure generic profile data securely mapping pagination boundaries explicitly.
"""

from core.repositories.base import UserRepository

async def get_users_list(user_repo: UserRepository, skip: int = 0, limit: int = 100):
    """
    Retrieves global user clusters securely abstracting limit caps ensuring memory
    consumption bounds universally natively decoupled through the Repo Interface.
    """
    return await user_repo.get_users(skip=skip, limit=limit)
