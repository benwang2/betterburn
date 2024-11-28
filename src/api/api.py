from typing import Union

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse

from pysteamsignin.steamsignin import SteamSignIn

from db.auth.utils import create_or_extend_session, is_valid_session
from config import Config

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

app = FastAPI()
cfg = Config()


@app.post("/api/session/")
def begin_auth(request: Request):
    data = request.json()
    discord_id = data.get("discord_id")

    if not discord_id:
        raise HTTPException(status_code=400, detail="No discord id was provided")

    session_id = create_or_extend_session(discord_id)
    return {"sessionId": session_id}


@app.get("/api/link/")
def link(sessionId: Union[str, None] = None):

    if sessionId is None:
        raise HTTPException(status_code=400, detail="No session id was provided")

    if not is_valid_session(session_id=sessionId):
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    redirect_url = f"http://{cfg.api_url}/auth"
    if sessionId:
        redirect_url += f"?sessionId={sessionId}"
    encodedData = steamLogin.ConstructURL(redirect_url)

    return steamLogin.RedirectUser(encodedData)


@app.get("/api/auth/")
def auth(request: Request, sessionId: str):

    if sessionId is None:
        raise HTTPException(status_code=400, detail="No session id was provided")

    if not is_valid_session(session_id=sessionId):
        raise HTTPException(status_code=400, detail="Session id is invalid")

    steamLogin = SteamSignIn()
    steamID = steamLogin.ValidateResults(request.query_params)

    print(f"SteamID = {steamID}")

    return HTMLResponse("Authenticated")


uvicorn.run(app, host="0.0.0.0", port=8000)
