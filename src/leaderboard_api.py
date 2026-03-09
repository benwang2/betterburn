import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import requests

from .config import Config
from .custom_logger import CustomLogger as Logger


class LeaderboardApiError(Exception):
    pass


class LeaderboardApiBadRequestError(LeaderboardApiError):
    pass


class LeaderboardApiNotFoundError(LeaderboardApiError):
    pass


class LeaderboardApiUnavailableError(LeaderboardApiError):
    pass


@dataclass(frozen=True)
class LeaderboardStanding:
    steam_id: str
    playfab_id: str
    stat_value: int
    position: int
    timestamp: str


@dataclass(frozen=True)
class LeaderboardMapping:
    steam_id: str
    playfab_id: str


class LeaderboardApiClient:
    def __init__(self, base_url: str | None = None, timeout: int = 10):
        self.base_url = (base_url or Config.leaderboard_api_base_url).rstrip("/")
        self.timeout = timeout
        self.logger = Logger("leaderboard_api")

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _parse_json(self, response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {}
        except ValueError:
            return {}

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._build_url(path)
        headers = {"X-Request-ID": str(uuid4())}

        try:
            response = requests.request(method=method, url=url, json=json, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            self.logger.error("Leaderboard API request failed", method=method, url=url, error=str(exc))
            raise LeaderboardApiUnavailableError("Leaderboard API is unavailable") from exc

        payload = self._parse_json(response)
        error_message = payload.get("error", "Leaderboard API request failed")

        if response.status_code == 404:
            raise LeaderboardApiNotFoundError(error_message)
        if response.status_code in (400, 422):
            raise LeaderboardApiBadRequestError(error_message)
        if response.status_code >= 500:
            raise LeaderboardApiUnavailableError(error_message)
        if response.status_code >= 300:
            raise LeaderboardApiError(error_message)

        return payload

    def get_health(self) -> dict[str, Any]:
        return self._request("GET", "/healthz")

    def get_standing(self, steam_id: int | str) -> LeaderboardStanding:
        payload = self._request("GET", f"/leaderboard/{steam_id}")
        return LeaderboardStanding(
            steam_id=str(payload["steam_id"]),
            playfab_id=str(payload["playfab_id"]),
            stat_value=int(payload["stat_value"]),
            position=int(payload["position"]),
            timestamp=str(payload["timestamp"]),
        )

    def create_mapping(self, steam_id: int | str) -> LeaderboardMapping:
        payload = self._request("POST", "/mappings", json={"steam_id": str(steam_id)})
        return LeaderboardMapping(
            steam_id=str(payload["steam_id"]),
            playfab_id=str(payload["playfab_id"]),
        )

    async def get_standing_async(self, steam_id: int | str) -> LeaderboardStanding:
        return await asyncio.to_thread(self.get_standing, steam_id)

    async def create_mapping_async(self, steam_id: int | str) -> LeaderboardMapping:
        return await asyncio.to_thread(self.create_mapping, steam_id)

    async def get_health_async(self) -> dict[str, Any]:
        return await asyncio.to_thread(self.get_health)


client = LeaderboardApiClient()