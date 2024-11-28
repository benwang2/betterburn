from sqlalchemy import Column, BigInteger, create_engine
from ..base import Base


class User(Base):
    __tablename__ = "discord"
    user_id = Column(BigInteger, primary_key=True, nullable=False)
    steam_id = Column(BigInteger, nullable=False)
