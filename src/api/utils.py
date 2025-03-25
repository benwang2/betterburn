from bridge import get_ext_api_url


def generate_link_url(session_id):
    return f"https://{get_ext_api_url()}/api/link?sessionId={session_id}"
