from typing import List, Callable
from datetime import datetime, timezone

import discord
from discord import Message
from config import Config


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


sessions: List[LinkedSession] = []


def find_linked_session(session_id) -> LinkedSession | None:
    for sess in sessions:
        if sess.session_id == session_id:
            return sess

    return None


def create_linked_session(session_id: str, discord_id: str) -> LinkedSession:
    sess = LinkedSession(session_id=session_id, discord_id=discord_id)
    sessions.append(sess)

    return sess


def remove_linked_session_by_id(session_id: str):
    for sess in sessions:
        if sess.session_id == session_id:
            sessions.remove(sess)
            break


def cull_expired_linked_sessions():
    sessions_to_cull = [
        sess
        for sess in sessions
        if (datetime.now(timezone.utc) - sess.created_at).seconds > 60
    ]
    for sess in sessions_to_cull:
        sessions.remove(sess)


def set_api_url(api_url: str):
    Config.api_url = api_url
