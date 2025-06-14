from sqlalchemy import BigInteger, Column, ForeignKey, SmallInteger

from ..base import Base


class UserTable(Base):
    __tablename__ = "user"
    user_id = Column(BigInteger, primary_key=True, nullable=False)
    steam_id = Column(BigInteger, nullable=False)


class RoleTable(Base):
    __tablename__ = "role"
    guild_id = Column(BigInteger, nullable=False)
    role_id = Column(BigInteger, primary_key=True, nullable=False)
    rank = Column(SmallInteger, nullable=False)


class MembershipTable(Base):
    __tablename__ = "membership"
    user_id = Column(BigInteger, ForeignKey(UserTable.user_id), primary_key=True, nullable=False)
    guild_id = Column(BigInteger, nullable=False)
