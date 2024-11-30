from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base

from .discord import models
from .cache import models


# SQLite engine setup
DATABASE_URL = "sqlite:///betterburn.db"
engine = create_engine(DATABASE_URL)

# Session factory
SQLAlchemySession = sessionmaker(bind=engine)


# Initialize database
def init_db():
    Base.metadata.create_all(engine)
