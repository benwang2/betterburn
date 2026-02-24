from typing import Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pysteamsignin.steamsignin import SteamSignIn

from ..bridge import (
    find_linked_session,
    get_ext_api_url,
    remove_linked_session_by_id,
)
from ..config import Config
from ..custom_logger import CustomLogger
from ..db.discord.utils import link_user
from ..db.session.utils import end_session, get_session, is_valid_session
from .health import get_health_status

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

logger = CustomLogger("fastapi")
app = FastAPI()


@app.get("/healthz")
async def healthz():
    """Comprehensive health check endpoint for load balancers and monitoring."""
    return get_health_status()


@app.get("/api/link/")
async def link(sessionId: Union[str, None] = None):
    if sessionId is None:
        logger.warning("Link request without session ID")
        raise HTTPException(status_code=400, detail="No session id was provided")

    if not is_valid_session(session_id=sessionId):
        logger.warning("Invalid session ID provided", session_id=sessionId)
        raise HTTPException(status_code=400, detail="Session id is invalid")

    logger.info("Redirecting to Steam OpenID", session_id=sessionId)
    steamLogin = SteamSignIn()
    redirect_url = f"https://{get_ext_api_url()}/api/auth"
    if sessionId:
        redirect_url += f"?sessionId={sessionId}"
    encodedData = steamLogin.ConstructURL(redirect_url)

    return steamLogin.RedirectUser(encodedData)


@app.get("/api/auth")
async def auth(sessionId: str, request: Request):
    if sessionId is None:
        logger.warning("Auth callback without session ID")
        raise HTTPException(status_code=400, detail="No session id was provided")

    session = get_session(session_id=sessionId)

    if session is None:
        logger.warning("Auth callback with invalid session", session_id=sessionId)
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    steamID = steamLogin.ValidateResults(request.query_params)

    logger.info("Steam authentication successful", discord_id=session.discord_id, steam_id=steamID)
    await link_user(user_id=session.discord_id, steam_id=steamID)

    linked_session = find_linked_session(session_id=sessionId)

    if linked_session:
        logger.debug("Firing linked session event", session_id=linked_session.session_id)
        await linked_session.event(steamID)
        remove_linked_session_by_id(linked_session.session_id)

    end_session(session_id=sessionId)

    return HTMLResponse("Authenticated - you may now close this window.")


def start():
    logger.info("Starting FastAPI server", host="0.0.0.0", port=Config.application_port)
    uvicorn.run(app, host="0.0.0.0", port=Config.application_port)
