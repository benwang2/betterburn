import csv
import datetime
from datetime import timezone as tz
from datetime import datetime as dt

from ..database import SQLAlchemySession
from .models import Session as Auth
from config import Config

cfg = Config()


def get_session(discord_id) -> Auth | None:
    session = SQLAlchemySession()
    auth_session = session.query(Auth).filter_by(discord_id=discord_id).first()
    session.close()

    return auth_session


def create_or_extend_session(discord_id):
    session = SQLAlchemySession()
    auth_session = session.query(Auth).filter_by(discord_id=discord_id).first()

    if auth_session:
        auth_session.expires_at = dt.now(tz.utc) + datetime.timedelta(
            minutes=cfg.session_duration
        )
    else:
        auth_session = Auth(discord_id=discord_id)
        session.add(auth_session)

    sess_id = auth_session.session_id

    session.commit()
    session.close()

    return sess_id


def cull_expired_sessions():
    session = SQLAlchemySession()
    now = dt.now(tz.utc)
    expired_sessions = session.query(Auth).filter(Auth.expires_at < now).all()

    for expired_session in expired_sessions:
        session.delete(expired_session)

    session.commit()
    session.close()


def is_valid_session(session_id):
    session = SQLAlchemySession()
    auth_session = session.query(Auth).filter_by(session_id=session_id).first()
    session.close()

    if auth_session:  # and auth_session.expires_at > dt.now(tz.utc):
        return True

    return False
