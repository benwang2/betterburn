from sqlalchemy import Column, BigInteger, Integer, TIMESTAMP
from ..base import Base
from datetime import datetime


# Cache table
class LeaderboardRow(Base):
    __tablename__ = "cache"
    steam_id = Column(BigInteger, primary_key=True, autoincrement=False)
    score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)


# Metadata table
class Metadata(Base):
    __tablename__ = "metadata"
    updated = Column(TIMESTAMP, primary_key=True, default=datetime.utcnow)
    player_count = Column(Integer, nullable=False)
