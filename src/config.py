from yaml import safe_load


def load_cfg() -> dict:
    with open("./config.yaml", "r") as f:
        return safe_load(f)


cfg = load_cfg()


class Config:
    api_url: str = cfg["api_url"]
    app_id: str = cfg["app_id"]
    leaderboard_id: str = cfg["leaderboard_id"]
    session_duration: str = cfg["session_duration"]

    def __str__(self) -> str:
        return f'<api_url="{self.api_url}" app_id={self.app_id} leaderboard_id={self.leaderboard_id} session_duration={self.session_duration}>'
