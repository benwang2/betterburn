from sqlalchemy import Column, BigInteger, TIMESTAMP, VARCHAR
from ..base import Base

import datetime
from datetime import datetime as dt
from datetime import timezone as tz
from uuid import uuid4 as uuid

from config import Config


class Session(Base):
    __tablename__ = "sessions"
    discord_id = Column(BigInteger, primary_key=True, autoincrement=False)
    session_id = Column(VARCHAR(36), default=lambda _: str(uuid()))
    expires_at = Column(
        TIMESTAMP,
        default=lambda _: dt.now(tz.utc) + datetime.timedelta(Config.session_duration),
    )

    def __str__(self):
        return f"<Session discord_id={self.discord_id} session_id={self.session_id} expires_at={self.expires_at}>"
