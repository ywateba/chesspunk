from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

# Association table for Many-to-Many relationship (Players <-> Competitions)
competition_players = Table(
    'competition_players', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('competition_id', Integer, ForeignKey('competitions.id'))
)

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="open") # open, active, finished
    
    # Relationships
    players = relationship("User", secondary=competition_players, back_populates="competitions")
    matches = relationship("Match", back_populates="competition")