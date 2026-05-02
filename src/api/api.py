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
from ..leaderboard_api import LeaderboardApiError, is_leaderboard_api_enabled
from ..leaderboard_api import client as leaderboard_api
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

    linked_session = find_linked_session(session_id=sessionId)

    if linked_session is None:
        logger.warning("Invalid session ID provided", session_id=sessionId)
        raise HTTPException(status_code=400, detail="Session id is invalid")

    logger.debug("Redirecting to Steam OpenID", session_id=sessionId, discord_id=linked_session.discord_id)
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

    linked_session = find_linked_session(session_id=sessionId)

    if linked_session is None:
        logger.warning("Auth callback with invalid session", session_id=sessionId)
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    steamID = steamLogin.ValidateResults(request.query_params)

    logger.info("Steam authentication successful", discord_id=linked_session.discord_id, steam_id=steamID)
    await link_user(user_id=linked_session.discord_id, steam_id=steamID)

    mapping_message = None

    if is_leaderboard_api_enabled():
        try:
            mapping = await leaderboard_api.create_mapping_async(steamID)
            logger.info(
                "Created leaderboard mapping",
                discord_id=linked_session.discord_id,
                steam_id=mapping.steam_id,
                playfab_id=mapping.playfab_id,
            )
        except LeaderboardApiError as exc:
            mapping_message = (
                "Your Steam account was linked, but leaderboard mapping could not be confirmed yet. "
                "If `/verify` fails, please try again shortly."
            )
            logger.warning(
                "Failed to create leaderboard mapping after link",
                discord_id=linked_session.discord_id,
                steam_id=steamID,
                error=str(exc),
            )

    logger.debug("Firing linked session event", session_id=linked_session.session_id)
    await linked_session.event(steamID, mapping_message=mapping_message)
    remove_linked_session_by_id(linked_session.session_id)

    if mapping_message:
        return HTMLResponse(f"Authenticated - you may now close this window. {mapping_message}")

    return HTMLResponse("Authenticated - you may now close this window.")


def start():
    logger.info("Starting FastAPI server", host="0.0.0.0", port=Config.application_port)
    uvicorn.run(app, host="0.0.0.0", port=Config.application_port)
