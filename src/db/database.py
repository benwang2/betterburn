from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import Config
from .base import Base

# SQLite engine setup — override via DATABASE_URL env var (e.g. for Docker volumes)
DATABASE_URL = Config.database_url
engine = create_engine(DATABASE_URL)

# Session factory
SQLAlchemySession = sessionmaker(bind=engine)


# Initialize database
def init_db():
    Base.metadata.create_all(engine)
