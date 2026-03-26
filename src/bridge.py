from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Callable

from .config import Config
from .custom_logger import logger


class LinkedSession:
    created_at: datetime
    session_id: str
    discord_id: str

    handler: Callable

    def __init__(self, session_id: str, discord_id: str):
        self.created_at = datetime.now(timezone.utc)
        self.session_id = session_id
        self.discord_id = discord_id

    def setEventHandler(self, handler: Callable):
        self.handler = handler

    async def event(self, *args, **kwargs):
        await self.handler(*args, **kwargs)


_lock = threading.Lock()
_sessions_by_id: dict[str, LinkedSession] = {}


def find_linked_session(session_id: str) -> LinkedSession | None:
    with _lock:
        return _sessions_by_id.get(session_id)


def create_linked_session(session_id: str, discord_id: str) -> LinkedSession:
    sess = LinkedSession(session_id=session_id, discord_id=discord_id)
    with _lock:
        _sessions_by_id[session_id] = sess
    logger.debug("Created linked session", session_id=session_id, discord_id=discord_id)
    return sess


def remove_linked_session_by_id(session_id: str):
    with _lock:
        _sessions_by_id.pop(session_id, None)


def cull_expired_linked_sessions() -> int:
    now = datetime.now(timezone.utc)

    # Default: keep the in-memory bridge session alive roughly as long as the
    # underlying DB session duration. Ensure we also respect the view timeout.
    ttl_seconds = max(60, int(getattr(Config, "session_duration", 60)))
    cutoff = now - timedelta(seconds=ttl_seconds)

    with _lock:
        expired_ids = [sid for sid, sess in _sessions_by_id.items() if sess.created_at < cutoff]
        for sid in expired_ids:
            _sessions_by_id.pop(sid, None)

    if expired_ids:
        logger.debug("Culled expired linked sessions", count=len(expired_ids))
    return len(expired_ids)


def count_linked_sessions() -> int:
    """Return current number of active in-memory linked sessions."""

    with _lock:
        return len(_sessions_by_id)


def set_ext_api_url(api_url: str):
    Config.api_url = api_url


def get_ext_api_url():
    return Config.api_url
