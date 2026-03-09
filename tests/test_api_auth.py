from types import SimpleNamespace

import pytest

from src.api import api as api_module


class DummySteamSignIn:
    def ValidateResults(self, query_params):
        return "76561198000000000"


class DummyLinkedSession:
    def __init__(self):
        self.session_id = "session-123"
        self.args = None
        self.kwargs = None

    async def event(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


@pytest.mark.asyncio
async def test_auth_creates_mapping_after_link(monkeypatch):
    linked_session = DummyLinkedSession()
    calls = {"link_user": None, "removed": None, "ended": None, "mapped": None}

    async def fake_link_user(user_id, steam_id):
        calls["link_user"] = (user_id, steam_id)

    async def fake_create_mapping_async(steam_id):
        calls["mapped"] = steam_id
        return SimpleNamespace(steam_id=steam_id, playfab_id="PLAYFAB123")

    monkeypatch.setattr(api_module, "SteamSignIn", DummySteamSignIn)
    monkeypatch.setattr(api_module, "is_leaderboard_api_enabled", lambda: True)
    monkeypatch.setattr(api_module, "get_session", lambda session_id: SimpleNamespace(discord_id=123))
    monkeypatch.setattr(api_module, "link_user", fake_link_user)
    monkeypatch.setattr(api_module.leaderboard_api, "create_mapping_async", fake_create_mapping_async)
    monkeypatch.setattr(api_module, "find_linked_session", lambda session_id: linked_session)
    monkeypatch.setattr(
        api_module, "remove_linked_session_by_id", lambda session_id: calls.__setitem__("removed", session_id)
    )
    monkeypatch.setattr(api_module, "end_session", lambda session_id: calls.__setitem__("ended", session_id))

    response = await api_module.auth("session-123", SimpleNamespace(query_params={}))

    assert calls["link_user"] == (123, "76561198000000000")
    assert calls["mapped"] == "76561198000000000"
    assert linked_session.args == ("76561198000000000",)
    assert linked_session.kwargs == {"mapping_message": None}
    assert calls["removed"] == "session-123"
    assert calls["ended"] == "session-123"
    assert response.body == b"Authenticated - you may now close this window."


@pytest.mark.asyncio
async def test_auth_skips_mapping_when_api_disabled(monkeypatch):
    linked_session = DummyLinkedSession()
    calls = {"link_user": None, "removed": None, "ended": None, "mapped": False}

    async def fake_link_user(user_id, steam_id):
        calls["link_user"] = (user_id, steam_id)

    async def fake_create_mapping_async(steam_id):
        calls["mapped"] = True
        return SimpleNamespace(steam_id=steam_id, playfab_id="PLAYFAB123")

    monkeypatch.setattr(api_module, "SteamSignIn", DummySteamSignIn)
    monkeypatch.setattr(api_module, "is_leaderboard_api_enabled", lambda: False)
    monkeypatch.setattr(api_module, "get_session", lambda session_id: SimpleNamespace(discord_id=123))
    monkeypatch.setattr(api_module, "link_user", fake_link_user)
    monkeypatch.setattr(api_module.leaderboard_api, "create_mapping_async", fake_create_mapping_async)
    monkeypatch.setattr(api_module, "find_linked_session", lambda session_id: linked_session)
    monkeypatch.setattr(api_module, "remove_linked_session_by_id", lambda session_id: calls.__setitem__("removed", session_id))
    monkeypatch.setattr(api_module, "end_session", lambda session_id: calls.__setitem__("ended", session_id))

    response = await api_module.auth("session-123", SimpleNamespace(query_params={}))

    assert calls["link_user"] == (123, "76561198000000000")
    assert calls["mapped"] is False
    assert linked_session.kwargs == {"mapping_message": None}
    assert response.body == b"Authenticated - you may now close this window."
