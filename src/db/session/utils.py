import csv
import datetime
from datetime import timezone as tz
from datetime import datetime as dt

from ..database import SQLAlchemySession
from .models import Session
from config import Config

cfg = Config()


def get_session_by_user(discord_id) -> Session | None:
    db = SQLAlchemySession()

    session = db.query(Session).filter_by(discord_id=discord_id).first()

    db.close()

    return session


def get_session(session_id) -> Session | None:
    db = SQLAlchemySession()

    session = db.query(Session).filter_by(session_id=session_id).first()

    db.close()

    return session


def create_or_extend_session(discord_id):
    db = SQLAlchemySession()

    session = db.query(Session).filter_by(discord_id=discord_id).first()

    if session:
        session.expires_at = dt.now(tz.utc) + datetime.timedelta(
            minutes=cfg.session_duration
        )
    else:
        session = Session(discord_id=discord_id)
        db.add(session)
        db.flush()

    session_id = session.session_id

    db.commit()
    db.close()

    return session_id


def end_session(session_id):
    db = SQLAlchemySession()

    session = db.query(Session).filter_by(session_id=session_id).first()

    db.delete(session)

    db.commit()
    db.close()


def cull_expired_sessions():
    db = SQLAlchemySession()
    now = dt.now(tz.utc)
    expired_sessions = db.query(Session).filter(Session.expires_at < now).all()

    for expired_session in expired_sessions:
        db.delete(expired_session)

    db.commit()
    db.close()


def delete_all_sessions():
    db = SQLAlchemySession()
    expired_sessions = db.query(Session).all()

    for expired_session in expired_sessions:
        db.delete(expired_session)

    db.commit()
    db.close()


def is_valid_session(session_id):
    db = SQLAlchemySession()
    auth_session = db.query(Session).filter_by(session_id=session_id).first()
    db.close()

    if auth_session:  # and auth_session.expires_at > dt.now(tz.utc):
        return True

    return False
