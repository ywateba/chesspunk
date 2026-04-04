import os, sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.db.database import get_db
from core.db.models import Base
from routers.main import app

# Determine database engine
DB_ENGINE = os.getenv("DB_ENGINE", "SQL")
print(f"Using database engine: {DB_ENGINE}")

if DB_ENGINE == "SQL":
    # Use an in-memory SQLite database for testing via aiosqlite
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
    print(f"Using SQL test database at: {SQLALCHEMY_DATABASE_URL}")

    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

    @pytest_asyncio.fixture(scope="function")
    async def db_session():
        """
        Fixture to create a new async database session for each test function.
        Creates all tables via run_sync, yields the session, then drops all tables.
        """
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as db:
            yield db

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

elif DB_ENGINE == "NOSQL":
    # Import NoSQL dependencies only when needed
    from mongomock_motor import AsyncMongoMockClient
    from beanie import init_beanie
    import mongomock

    # Patch mongomock.Database to ignore `authorizedCollections` missing keyword argument
    _original_list_collection_names = mongomock.Database.list_collection_names
    def _patched_list_collection_names(self, *args, **kwargs):
        kwargs.pop('authorizedCollections', None)
        kwargs.pop('nameOnly', None)
        return _original_list_collection_names(self, *args, **kwargs)
    mongomock.Database.list_collection_names = _patched_list_collection_names

    from core.db.documents import UserDocument, CompetitionDocument, MatchDocument, CommunityDocument

    @pytest_asyncio.fixture(scope="function", autouse=True)
    async def init_mock_mongodb():
        """
        Fixture to initialize mock MongoDB for NoSQL tests.
        """
        client = AsyncMongoMockClient()
        await init_beanie(
            database=client.get_database("test_db"),
            document_models=[UserDocument, CompetitionDocument, MatchDocument, CommunityDocument]
        )
        yield

    @pytest_asyncio.fixture(scope="function")
    async def db_session():
        """
        For NoSQL, we don't need a SQL session, but we provide this fixture for compatibility.
        Tests that need database operations will use the repositories directly.
        """
        yield None

else:
    raise ValueError(f"Unsupported DB_ENGINE: {DB_ENGINE}. Must be 'SQL' or 'NOSQL'")

@pytest_asyncio.fixture(scope="function")
async def test_client(db_session):
    """
    Fixture to create an AsyncClient with the get_db dependency overridden.
    For NoSQL, get_db is not used, but we still override it for compatibility.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.state.limiter.enabled = False
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    del app.dependency_overrides[get_db]