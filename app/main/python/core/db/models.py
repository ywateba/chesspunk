from sqlalchemy import Column, Integer, String, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from core.db.database import Base
import enum

# Association table for Many-to-Many relationship (Players <-> Competitions)
competition_players = Table(
    'competition_players', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('competition_id', Integer, ForeignKey('competitions.id'))
)

class MatchResult(str, enum.Enum):
    WHITE_WINS = "1-0"
    BLACK_WINS = "0-1"
    DRAW = "1/2-1/2"
    PENDING = "*"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="player")
    elo = Column(Integer, default=1200)
    
    # Relationships
    competitions = relationship("Competition", secondary=competition_players, back_populates="players")

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    format = Column(String, default="round_robin")
    status = Column(String, default="open") # open, active, finished
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True)
    
    # Relationships
    players = relationship("User", secondary=competition_players, back_populates="competitions")
    matches = relationship("Match", back_populates="competition")
    community = relationship("Community", back_populates="competitions")

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"))
    
    # Foreign keys for players
    white_player_id = Column(Integer, ForeignKey("users.id"))
    black_player_id = Column(Integer, ForeignKey("users.id"))
    
    result = Column(String, default=MatchResult.PENDING)
    pgn_blueprint = Column(String, nullable=True) # The chess blueprint

    # Relationships
    competition = relationship("Competition", back_populates="matches")
    white_player = relationship("User", foreign_keys=[white_player_id])
    black_player = relationship("User", foreign_keys=[black_player_id])

class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("CommunityMember", back_populates="community")
    competitions = relationship("Competition", back_populates="community")

class CommunityMember(Base):
    __tablename__ = "community_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    community_id = Column(Integer, ForeignKey("communities.id"))
    role = Column(String, default="member") # "owner", "admin", "member"
    rank = Column(Integer, default=0)
    
    user = relationship("User", foreign_keys=[user_id])
    community = relationship("Community", back_populates="members")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    
    author = relationship("User")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String) # "post" or "match"
    entity_id = Column(Integer)
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    
    author = relationship("User")
