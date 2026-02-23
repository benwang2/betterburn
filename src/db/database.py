from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import Config
from ..custom_logger import CustomLogger
from .base import Base

logger = CustomLogger("database")

# SQLite engine setup — override via DATABASE_URL env var (e.g. for Docker volumes)
DATABASE_URL = Config.database_url
engine = create_engine(DATABASE_URL)

# Session factory
SQLAlchemySession = sessionmaker(bind=engine)


# Initialize database
def init_db():
    logger.info("Initializing database", database_url=DATABASE_URL)
    Base.metadata.create_all(engine)
    logger.info("Database initialized")
