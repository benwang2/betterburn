from toml import load

def load_cfg() -> dict:
    with open("./config.toml", "r") as f:
        return load(f)


cfg = load_cfg()


class Config:
    api_url: str = cfg["api_url"]
    ext_api_url: str = ""
    application_port: str = cfg["application_port"]
    app_id: str = cfg["app_id"]
    discord_token: str = cfg["discord_token"]
    ngrok_auth_token: str = cfg["ngrok_auth_token"]
    leaderboard_id: str = cfg["leaderboard_id"]
    cache_update_interval: int = cfg["cache_update_interval"]
    session_duration: str = cfg["session_duration"]
    test_guild: str = cfg["test_guild"]
    roles = cfg["roles"]

    def __str__(self) -> str:
        return f'<api_url="{self.api_url}" app_id={self.app_id} leaderboard_id={self.leaderboard_id} session_duration={self.session_duration}>'


if __name__ == "__main__":
    print(cfg)
