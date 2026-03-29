import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
import mongomock

# Patch mongomock.Database to ignore `authorizedCollections` missing keyword argument requested by Beanie>1.20 automatically
_original_list_collection_names = mongomock.Database.list_collection_names
def _patched_list_collection_names(self, *args, **kwargs):
    kwargs.pop('authorizedCollections', None)
    kwargs.pop('nameOnly', None)
    return _original_list_collection_names(self, *args, **kwargs)
mongomock.Database.list_collection_names = _patched_list_collection_names

from core.schemas import schemas
from core.db.documents import UserDocument, CompetitionDocument, MatchDocument
from core.repositories.nosql.user_repo import MongoUserRepository
from core.repositories.nosql.competition_repo import MongoCompetitionRepository
from core.repositories.nosql.match_repo import MongoMatchRepository

@pytest_asyncio.fixture(autouse=True)
async def init_mock_mongodb():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[UserDocument, CompetitionDocument, MatchDocument]
    )
    yield

@pytest.mark.asyncio
async def test_mongo_user_repository():
    repo = MongoUserRepository()
    user_in = schemas.UserCreate(username="nosql_user", email="nosql@test.com", password="pwd")
    user = await repo.create_user(user_in, "hashed")
    
    assert user.id is not None
    assert user.username == "nosql_user"
    assert user.email == "nosql@test.com"
    
    fetched = await repo.get_user_by_email("nosql@test.com")
    assert fetched is not None
    assert fetched.id == user.id

    fetched_by_name = await repo.get_user_by_username("nosql_user")
    assert fetched_by_name is not None
    assert fetched_by_name.id == user.id

@pytest.mark.asyncio
async def test_mongo_competition_repository():
    repo = MongoCompetitionRepository()
    comp_in = schemas.CompetitionCreate(name="Mongo Tourney")
    comp = await repo.create_competition(comp_in)
    
    assert comp.name == "Mongo Tourney"
    
    # Assert id generation translates seamlessly to string conversions native to Beanie
    assert str(comp.id) is not None
    
    fetched = await repo.get_competition(str(comp.id))
    assert fetched is not None
    assert fetched.name == "Mongo Tourney"

@pytest.mark.asyncio
async def test_mongo_match_repository():
    user_repo = MongoUserRepository()
    comp_repo = MongoCompetitionRepository()
    match_repo = MongoMatchRepository()
    
    # 1. Setup mock competition & users
    comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Mongo Match"))
    p1 = await user_repo.create_user(schemas.UserCreate(username="p1", email="p1@m.com", password="x"), "h")
    p2 = await user_repo.create_user(schemas.UserCreate(username="p2", email="p2@m.com", password="x"), "h")
    
    # 2. Add players to competition natively using Repo mappings
    await comp_repo.add_player_to_competition(comp, p1)
    await comp_repo.add_player_to_competition(comp, p2)
    
    class FakeMatchPayload:
        def __init__(self, c_id, w_id, b_id, res):
            self.competition_id = c_id
            self.white_player_id = w_id
            self.black_player_id = b_id
            self.result = res
            
    payload = FakeMatchPayload(comp.id, p1.id, p2.id, "*")
    created = await match_repo.create_matches([payload])
    
    assert len(created) == 1
    m1 = created[0]
    
    # 3. Simulate updating the match blueprint
    updated = await match_repo.update_match(m1, "1-0", "1. e4")
    assert updated.result == "1-0"
    assert updated.pgn_blueprint == "1. e4"
    
    # 4. Verify native retrieval behaviors emulate SQLAlchemy relation fetches implicitly through manual hooks
    refetched_comp = await comp_repo.get_competition(str(comp.id))
    assert len(refetched_comp.players) == 2
    assert len(refetched_comp.matches) == 1
