"""
SQL Database Configuration
==========================
Bootstraps asynchronous SQLAlchemy engines and declarative base classes exclusively.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings

# This creates a file named 'test.db' in the same folder
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = None

# connect_args={"check_same_thread": False} is needed only for SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Dependency to get DB session in endpoints
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
