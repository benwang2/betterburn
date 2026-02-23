import os

from dotenv import load_dotenv

load_dotenv()


def _parse_int_list(value: str) -> list[int]:
    """Parse a comma-separated string of ints, e.g. '123,456' → [123, 456]."""
    if not value or not value.strip():
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


class Config:
    api_url: str = os.environ.get("API_URL", "localhost")
    application_port: int = int(os.environ.get("APPLICATION_PORT", "80"))
    app_id: int = int(os.environ.get("APP_ID", "2217000"))
    leaderboard_id: int = int(os.environ.get("LEADERBOARD_ID", "16200142"))
    cache_update_interval: int = int(os.environ.get("CACHE_UPDATE_INTERVAL", "120"))
    session_duration: int = int(os.environ.get("SESSION_DURATION", "300"))
    discord_token: str = os.environ.get("DISCORD_TOKEN", "")
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///betterburn.db")
    # Comma-separated guild IDs, e.g. TEST_GUILD=123456789,987654321
    test_guild: list[int] = _parse_int_list(os.environ.get("TEST_GUILD", ""))

    def __str__(self) -> str:
        return f'<api_url="{self.api_url}" app_id={self.app_id} leaderboard_id={self.leaderboard_id} session_duration={self.session_duration}>'
