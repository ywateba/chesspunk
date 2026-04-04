"""
Tests for MongoDB Social Repository
===================================
Comprehensive test suite for MongoSocialRepository covering all operations.
"""

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
from core.db.documents import UserDocument, CommunityDocument, PostDocument, CommentDocument
from core.repositories.nosql.user_repo import MongoUserRepository
from core.repositories.nosql.community_repo import MongoCommunityRepository
from core.repositories.nosql.social_repo import MongoSocialRepository


@pytest_asyncio.fixture(autouse=True)
async def init_mock_mongodb():
    """Initialize mock MongoDB for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[UserDocument, CommunityDocument, PostDocument, CommentDocument]
    )
    yield


@pytest.mark.asyncio
class TestMongoSocialRepository:
    """Test suite for MongoSocialRepository."""

    @pytest.fixture
    async def social_repo(self):
        """Fixture providing a fresh social repository instance."""
        return MongoSocialRepository()

    @pytest.fixture
    async def user_repo(self):
        """Fixture providing a fresh user repository instance."""
        return MongoUserRepository()

    @pytest.fixture
    async def community_repo(self):
        """Fixture providing a fresh community repository instance."""
        return MongoCommunityRepository()

    async def test_create_post(self, social_repo, user_repo, community_repo):
        """Test creating a post in a community."""
        # Setup: Create community and user
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Create post
        post_content = "This is a test post about chess strategies!"
        post = await social_repo.create_post(community.id, owner.id, post_content)

        # Assertions
        assert post is not None
        assert post.id is not None
        assert str(post.community_id) == str(community.id)
        assert str(post.author_id) == str(owner.id)
        assert post.content == post_content
        assert post.created_at is not None

    async def test_get_posts(self, social_repo, user_repo, community_repo):
        """Test retrieving posts from a community."""
        # Setup
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Create multiple posts
        posts_data = [
            "First post about opening theory",
            "Second post about endgames",
            "Third post about tactics"
        ]

        created_posts = []
        for content in posts_data:
            post = await social_repo.create_post(community.id, owner.id, content)
            created_posts.append(post)

        # Retrieve posts
        retrieved_posts = await social_repo.get_posts(community.id)

        # Assertions
        assert len(retrieved_posts) == 3
        retrieved_contents = [p.content for p in retrieved_posts]
        for content in posts_data:
            assert content in retrieved_contents

    async def test_get_posts_pagination(self, social_repo, user_repo, community_repo):
        """Test retrieving posts with pagination."""
        # Setup
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Create 5 posts
        for i in range(5):
            await social_repo.create_post(community.id, owner.id, f"Post {i}")

        # Test pagination
        all_posts = await social_repo.get_posts(community.id, skip=0, limit=10)
        assert len(all_posts) == 5

        # Test with limit
        limited_posts = await social_repo.get_posts(community.id, skip=0, limit=2)
        assert len(limited_posts) == 2

        # Test with skip
        skipped_posts = await social_repo.get_posts(community.id, skip=2, limit=10)
        assert len(skipped_posts) == 3

    async def test_get_posts_empty_community(self, social_repo, user_repo, community_repo):
        """Test retrieving posts from community with no posts."""
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Empty Community", description="Test"),
            str(owner.id)
        )

        posts = await social_repo.get_posts(community.id)
        assert posts == []

    async def test_get_posts_different_communities(self, social_repo, user_repo, community_repo):
        """Test that posts are properly isolated between communities."""
        # Create two communities
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )

        comm1 = await community_repo.create_community(
            schemas.CommunityCreate(name="Community 1", description="Test"),
            str(owner.id)
        )
        comm2 = await community_repo.create_community(
            schemas.CommunityCreate(name="Community 2", description="Test"),
            str(owner.id)
        )

        # Create posts in each community
        await social_repo.create_post(comm1.id, owner.id, "Post in community 1")
        await social_repo.create_post(comm2.id, owner.id, "Post in community 2")

        # Verify isolation
        comm1_posts = await social_repo.get_posts(comm1.id)
        comm2_posts = await social_repo.get_posts(comm2.id)

        assert len(comm1_posts) == 1
        assert len(comm2_posts) == 1
        assert comm1_posts[0].content == "Post in community 1"
        assert comm2_posts[0].content == "Post in community 2"

    async def test_create_comment_on_post(self, social_repo, user_repo, community_repo):
        """Test creating a comment on a post."""
        # Setup
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        commenter = await user_repo.create_user(
            schemas.UserCreate(username="commenter", email="commenter@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Create post
        post = await social_repo.create_post(community.id, owner.id, "Test post")

        # Create comment on post
        comment_content = "Great post! I agree with your analysis."
        comment = await social_repo.create_comment("post", post.id, commenter.id, comment_content)

        # Assertions
        assert comment is not None
        assert comment.id is not None
        assert comment.entity_type == "post"
        assert str(comment.entity_id) == str(post.id)
        assert str(comment.author_id) == str(commenter.id)
        assert comment.content == comment_content
        assert comment.created_at is not None

    async def test_create_comment_on_match(self, social_repo, user_repo, community_repo):
        """Test creating a comment on a match."""
        from core.repositories.nosql.match_repo import MongoMatchRepository
        from core.repositories.nosql.competition_repo import MongoCompetitionRepository

        # Setup
        match_repo = MongoMatchRepository()
        comp_repo = MongoCompetitionRepository()

        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        commenter = await user_repo.create_user(
            schemas.UserCreate(username="commenter", email="commenter@test.com", password="pass"),
            "hash"
        )

        # Create competition and match
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Test Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="player1", email="p1@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="player2", email="p2@test.com", password="pass"),
            "hash2"
        )

        # Create match
        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        matches = await match_repo.create_matches([payload])
        match = matches[0]

        # Create comment on match
        comment_content = "What a brilliant sacrifice!"
        comment = await social_repo.create_comment("match", match.id, commenter.id, comment_content)

        # Assertions
        assert comment is not None
        assert comment.entity_type == "match"
        assert str(comment.entity_id) == str(match.id)
        assert str(comment.author_id) == str(commenter.id)
        assert comment.content == comment_content

    async def test_get_comments_on_post(self, social_repo, user_repo, community_repo):
        """Test retrieving comments on a post."""
        # Setup
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        commenters = []
        for i in range(3):
            commenter = await user_repo.create_user(
                schemas.UserCreate(username=f"commenter{i}", email=f"c{i}@test.com", password="pass"),
                "hash"
            )
            commenters.append(commenter)

        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Create post
        post = await social_repo.create_post(community.id, owner.id, "Test post")

        # Create multiple comments
        comments_data = [
            "First comment",
            "Second comment",
            "Third comment"
        ]

        created_comments = []
        for i, content in enumerate(comments_data):
            comment = await social_repo.create_comment("post", post.id, commenters[i].id, content)
            created_comments.append(comment)

        # Retrieve comments
        retrieved_comments = await social_repo.get_comments("post", post.id)

        # Assertions
        assert len(retrieved_comments) == 3
        retrieved_contents = [c.content for c in retrieved_comments]
        for content in comments_data:
            assert content in retrieved_contents

    async def test_get_comments_pagination(self, social_repo, user_repo, community_repo):
        """Test retrieving comments with pagination."""
        # Setup
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        commenter = await user_repo.create_user(
            schemas.UserCreate(username="commenter", email="commenter@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Create post
        post = await social_repo.create_post(community.id, owner.id, "Test post")

        # Create 5 comments
        for i in range(5):
            await social_repo.create_comment("post", post.id, commenter.id, f"Comment {i}")

        # Test pagination
        all_comments = await social_repo.get_comments("post", post.id, skip=0, limit=10)
        assert len(all_comments) == 5

        # Test with limit
        limited_comments = await social_repo.get_comments("post", post.id, skip=0, limit=2)
        assert len(limited_comments) == 2

        # Test with skip
        skipped_comments = await social_repo.get_comments("post", post.id, skip=2, limit=10)
        assert len(skipped_comments) == 3

    async def test_get_comments_empty_entity(self, social_repo, user_repo, community_repo):
        """Test retrieving comments from entity with no comments."""
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        post = await social_repo.create_post(community.id, owner.id, "Test post")

        comments = await social_repo.get_comments("post", post.id)
        assert comments == []

    async def test_comments_isolation_by_entity(self, social_repo, user_repo, community_repo):
        """Test that comments are properly isolated by entity type and ID."""
        from core.repositories.nosql.match_repo import MongoMatchRepository
        from core.repositories.nosql.competition_repo import MongoCompetitionRepository

        # Setup
        match_repo = MongoMatchRepository()
        comp_repo = MongoCompetitionRepository()

        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        commenter = await user_repo.create_user(
            schemas.UserCreate(username="commenter", email="commenter@test.com", password="pass"),
            "hash"
        )

        # Create community and post
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )
        post = await social_repo.create_post(community.id, owner.id, "Test post")

        # Create competition and match
        comp = await comp_repo.create_competition(schemas.CompetitionCreate(name="Test Comp"))
        user1 = await user_repo.create_user(
            schemas.UserCreate(username="player1", email="p1@test.com", password="pass"),
            "hash1"
        )
        user2 = await user_repo.create_user(
            schemas.UserCreate(username="player2", email="p2@test.com", password="pass"),
            "hash2"
        )

        class FakeMatchPayload:
            def __init__(self, c_id, w_id, b_id, res):
                self.competition_id = c_id
                self.white_player_id = w_id
                self.black_player_id = b_id
                self.result = res

        payload = FakeMatchPayload(comp.id, user1.id, user2.id, "*")
        matches = await match_repo.create_matches([payload])
        match = matches[0]

        # Create comments on different entities
        await social_repo.create_comment("post", post.id, commenter.id, "Comment on post")
        await social_repo.create_comment("match", match.id, commenter.id, "Comment on match")

        # Verify isolation
        post_comments = await social_repo.get_comments("post", post.id)
        match_comments = await social_repo.get_comments("match", match.id)

        assert len(post_comments) == 1
        assert len(match_comments) == 1
        assert post_comments[0].content == "Comment on post"
        assert match_comments[0].content == "Comment on match"
        assert post_comments[0].entity_type == "post"
        assert match_comments[0].entity_type == "match"

    async def test_social_data_integrity(self, social_repo, user_repo, community_repo):
        """Test that social data is stored and retrieved correctly."""
        owner = await user_repo.create_user(
            schemas.UserCreate(username="owner", email="owner@test.com", password="pass"),
            "hash"
        )
        commenter = await user_repo.create_user(
            schemas.UserCreate(username="commenter", email="commenter@test.com", password="pass"),
            "hash"
        )
        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Test Community", description="Test"),
            str(owner.id)
        )

        # Test post with complex content
        complex_post_content = """# Chess Opening Analysis

This is a detailed analysis of the Sicilian Defense:

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6

The Najdorf variation is one of the most popular and complex openings in chess.
It leads to rich, tactical positions that require deep understanding of chess principles.

## Key Ideas:
- Black prepares ...b5 with ...a6
- Flexible development
- Counter-attacking chances

What are your thoughts on this opening?"""
        post = await social_repo.create_post(community.id, owner.id, complex_post_content)

        # Test comment with special characters
        complex_comment_content = "Great analysis! 👍 I especially like how ♟️ prepares for the ♞ development. Have you tried 6. Bg5 instead of 6. Be3? #chess #opening"
        comment = await social_repo.create_comment("post", post.id, commenter.id, complex_comment_content)

        # Retrieve and verify
        retrieved_posts = await social_repo.get_posts(community.id)
        retrieved_comments = await social_repo.get_comments("post", post.id)

        assert len(retrieved_posts) == 1
        assert len(retrieved_comments) == 1
        assert retrieved_posts[0].content == complex_post_content
        assert retrieved_comments[0].content == complex_comment_content
        assert str(retrieved_posts[0].author_id) == str(owner.id)
        assert str(retrieved_comments[0].author_id) == str(commenter.id)

    async def test_multiple_authors_social_interaction(self, social_repo, user_repo, community_repo):
        """Test social interactions with multiple authors."""
        # Create multiple users
        users = []
        for i in range(4):
            user = await user_repo.create_user(
                schemas.UserCreate(username=f"user{i}", email=f"user{i}@test.com", password="pass"),
                f"hash{i}"
            )
            users.append(user)

        community = await community_repo.create_community(
            schemas.CommunityCreate(name="Social Community", description="Test"),
            str(users[0].id)
        )

        # User 0 creates a post
        post = await social_repo.create_post(community.id, users[0].id, "Original post")

        # Users 1, 2, 3 comment on the post
        for i in range(1, 4):
            await social_repo.create_comment("post", post.id, users[i].id, f"Comment from user {i}")

        # Verify all interactions
        retrieved_post = await social_repo.get_posts(community.id)
        retrieved_comments = await social_repo.get_comments("post", post.id)

        assert len(retrieved_post) == 1
        assert len(retrieved_comments) == 3

        # Check all authors are different
        post_author = str(retrieved_post[0].author_id)
        comment_authors = [str(c.author_id) for c in retrieved_comments]
        all_authors = [post_author] + comment_authors

        assert len(set(all_authors)) == 4  # All authors should be unique