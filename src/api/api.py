from typing import Union

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse

from pysteamsignin.steamsignin import SteamSignIn

from db.session.utils import is_valid_session, get_session, end_session

from db.discord.utils import link_user

from config import Config

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

app = FastAPI()
cfg = Config()


@app.get("/api/link/")
def link(sessionId: Union[str, None] = None):

    if sessionId is None:
        raise HTTPException(status_code=400, detail="No session id was provided")

    if not is_valid_session(session_id=sessionId):
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    redirect_url = f"http://{cfg.api_url}/api/auth"
    if sessionId:
        redirect_url += f"?sessionId={sessionId}"
    encodedData = steamLogin.ConstructURL(redirect_url)

    return steamLogin.RedirectUser(encodedData)


@app.get("/api/auth/")
async def auth(sessionId: str, request: Request):

    if sessionId is None:
        raise HTTPException(status_code=400, detail="No session id was provided")

    session = get_session(session_id=sessionId)

    if session is None:
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    steamID = steamLogin.ValidateResults(request.query_params)

    await link_user(user_id=session.discord_id, steam_id=steamID)
    end_session(session_id=sessionId)

    return HTMLResponse("Authenticated")


def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)
