from sqlalchemy import Column, Integer, String, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from database import Base
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
    
    # Relationships
    competitions = relationship("Competition", secondary=competition_players, back_populates="players")

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="open") # open, active, finished
    
    # Relationships
    players = relationship("User", secondary=competition_players, back_populates="competitions")
    matches = relationship("Match", back_populates="competition")

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
