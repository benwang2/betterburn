from config import Config

cfg = Config()


def generate_link_url(session_id):
    return f"http://{cfg.api_url}/api/link?sessionId={session_id}"
