import pytest
import requests

from src.leaderboard_api import (
    LeaderboardApiBadRequestError,
    LeaderboardApiClient,
    LeaderboardApiDisabledError,
    LeaderboardApiUnavailableError,
)


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_get_standing_returns_typed_result(monkeypatch):
    def fake_request(method, url, json=None, headers=None, timeout=None):
        assert method == "GET"
        assert url == "http://leaderboard.test/leaderboard/?sid=76561198000000000"
        assert json is None
        assert headers["X-Request-ID"]
        assert timeout == 10
        return DummyResponse(
            200,
            {
                "steam_id": "76561198000000000",
                "playfab_id": "PLAYFAB123",
                "stat_value": 1542,
                "position": 42,
                "timestamp": "2026-03-09T12:34:56+00:00",
            },
        )

    monkeypatch.setattr("src.leaderboard_api.requests.request", fake_request)

    client = LeaderboardApiClient(base_url="http://leaderboard.test")
    standing = client.get_standing("76561198000000000")

    assert standing.playfab_id == "PLAYFAB123"
    assert standing.stat_value == 1542
    assert standing.position == 42


def test_create_mapping_raises_bad_request(monkeypatch):
    def fake_request(method, url, json=None, headers=None, timeout=None):
        return DummyResponse(400, {"error": "steam_id must be a 17-digit number"})

    monkeypatch.setattr("src.leaderboard_api.requests.request", fake_request)

    client = LeaderboardApiClient(base_url="http://leaderboard.test")

    with pytest.raises(LeaderboardApiBadRequestError, match="17-digit"):
        client.create_mapping("bad-id")


def test_get_health_raises_unavailable_on_request_failure(monkeypatch):
    def fake_request(method, url, json=None, headers=None, timeout=None):
        raise requests.RequestException("connection failed")

    monkeypatch.setattr("src.leaderboard_api.requests.request", fake_request)

    client = LeaderboardApiClient(base_url="http://leaderboard.test")

    with pytest.raises(LeaderboardApiUnavailableError, match="unavailable"):
        client.get_health()


def test_client_is_disabled_without_base_url():
    client = LeaderboardApiClient(base_url=None)

    assert client.enabled is False

    with pytest.raises(LeaderboardApiDisabledError, match="not configured"):
        client.get_health()
