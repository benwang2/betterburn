from sqlalchemy import Column, BigInteger, SmallInteger
from ..base import Base


class UserTable(Base):
    __tablename__ = "user"
    user_id = Column(BigInteger, primary_key=True, nullable=False)
    steam_id = Column(BigInteger, nullable=False)
