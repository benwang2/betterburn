from config import Config

cfg = Config()


def generate_link_url(session_id):
    return f"{cfg.ext_api_url}/api/link?sessionId={session_id}"
