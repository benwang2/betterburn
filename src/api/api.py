from typing import Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pysteamsignin.steamsignin import SteamSignIn

from bridge import (
    find_linked_session,
    get_ext_api_url,
    remove_linked_session_by_id,
)
from config import Config

from ..db.discord.utils import link_user
from ..db.session.utils import end_session, get_session, is_valid_session

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

app = FastAPI()


@app.get("/api/link/")
async def link(sessionId: Union[str, None] = None):
    if sessionId is None:
        raise HTTPException(status_code=400, detail="No session id was provided")

    if not is_valid_session(session_id=sessionId):
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    redirect_url = f"https://{get_ext_api_url()}/api/auth"
    if sessionId:
        redirect_url += f"?sessionId={sessionId}"
    encodedData = steamLogin.ConstructURL(redirect_url)

    return steamLogin.RedirectUser(encodedData)


@app.get("/api/auth")
async def auth(sessionId: str, request: Request):
    if sessionId is None:
        raise HTTPException(status_code=400, detail="No session id was provided")

    session = get_session(session_id=sessionId)

    if session is None:
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    steamID = steamLogin.ValidateResults(request.query_params)

    await link_user(user_id=session.discord_id, steam_id=steamID)

    linked_session = find_linked_session(session_id=sessionId)

    if linked_session:
        print("Found session:" + linked_session.session_id)
        await linked_session.event(steamID)
        remove_linked_session_by_id(linked_session.session_id)

    end_session(session_id=sessionId)

    return HTMLResponse("Authenticated - you may now close this window.")


def start():
    uvicorn.run(app, host="0.0.0.0", port=Config.application_port)
