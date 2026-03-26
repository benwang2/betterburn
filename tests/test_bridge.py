from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src import bridge


def test_create_find_remove_linked_session():
    sess = bridge.create_linked_session(session_id="abc", discord_id="123")
    assert bridge.find_linked_session("abc") is sess

    bridge.remove_linked_session_by_id("abc")
    assert bridge.find_linked_session("abc") is None


def test_cull_expired_linked_sessions_respects_config(monkeypatch):
    # Make TTL small so we can cull deterministically.
    monkeypatch.setattr(bridge.Config, "session_duration", 60)

    s1 = bridge.create_linked_session(session_id="old", discord_id="1")
    s2 = bridge.create_linked_session(session_id="new", discord_id="2")

    # Force timestamps.
    s1.created_at = datetime.now(timezone.utc) - timedelta(seconds=61)
    s2.created_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    culled = bridge.cull_expired_linked_sessions()
    assert culled == 1
    assert bridge.find_linked_session("old") is None
    assert bridge.find_linked_session("new") is s2


def test_count_linked_sessions():
    # Ensure monotonic behavior for the helper.
    before = bridge.count_linked_sessions()
    bridge.create_linked_session(session_id="count", discord_id="1")
    assert bridge.count_linked_sessions() == before + 1
