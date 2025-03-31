from sqlalchemy import Column, BigInteger, Integer
from ..base import Base


# Cache table
class LeaderboardRow(Base):
    __tablename__ = "cache"
    steam_id = Column(BigInteger, primary_key=True, autoincrement=False)
    score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)


# Metadata table
class Metadata(Base):
    __tablename__ = "metadata"
    updated = Column(BigInteger, primary_key=True)
    player_count = Column(Integer, nullable=False)
