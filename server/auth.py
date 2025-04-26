from fastapi import APIRouter, Request
from fastapi.datastructures import URL
from fastapi.responses import Response, JSONResponse, HTMLResponse
from fastapi import Query
from starsessions import load_session, regenerate_session_id
from pydantic import BaseModel
import sys
import os
import random
import timeit
import base64
import requests
from dotenv import load_dotenv
load_dotenv()

# Client Keys
CLIENT_ID = os.environ.get("CLIENT_ID", None)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", None)
SCHEME = os.environ.get("SCHEME", "http")

if CLIENT_ID is None or CLIENT_SECRET is None:
    print(
        "Please set CLIENT_ID and CLIENT_SECRET environment variables to authenticate your app with spotify."
    )
    sys.exit(1)

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
class Token:
    token: str
    expiration: float
    refresh_token: str | None

    def __new__(cls, token: str, expiration: float, refresh_token: str | None = None):
        self = super().__new__(cls)
        self.token = token
        self.expiration = expiration
        self.refresh_token = refresh_token
        return self
    
    def is_valid(self) -> bool:
        return self.token is not None and timeit.default_timer() < (self.expiration - 2)
    
class ClientToken:
    token: Token = None
    def __new__(cls):
        cls.token = get_token(CLIENT_ID, CLIENT_SECRET, {"grant_type": "client_credentials"}, cls.token)
        return cls.token

#TODO: MAke BseeModel to include in session
class UserToken:
    token: Token = None
    def __new__(cls, code: str | None = None, redirect_uri: str | None = None):
        if cls.token is not None and cls.token.is_valid():
            return cls.token
        elif code is None or redirect_uri is None:
            raise ValueError("No token found. Please login first.")
        token_request_body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        cls.token = get_token(CLIENT_ID, CLIENT_SECRET, token_request_body, cls.token)
        return cls.token
        

def get_token(client_id: str, client_secret: str, payload: dict, token: Token | None = None):
    if token is not None and token.is_valid():
        return token
    if token is not None and token.refresh_token is not None:
        payload = { "refresh_token": token.refresh_token, "grant_type": "refresh_token"}
    client_token = base64.b64encode(
        "{}:{}".format(client_id, client_secret).encode("UTF-8")
    ).decode("ascii")
    headers = {
        "Authorization": "Basic {}".format(client_token),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    token_request = requests.post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)
    response = token_request.json()
    access_token = response["access_token"]
    expiration_date = timeit.default_timer() + response["expires_in"]
    refresh_token= response.get("refresh_token", None)
    return Token(token=access_token, expiration=expiration_date, refresh_token=refresh_token)


auth = APIRouter(prefix="/auth")

token: Token | None = None

def random_string(len: int) -> str:
    symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    string = ""
    for i in range(len):
        string + random.choice(symbols)
    return string

@auth.get("/login")
async def login(request: Request):
    await load_session(request)
    redirect_uri = request.url_for("callback")
    redirect_uri = redirect_uri.replace(scheme=SCHEME)
    state = random_string(32)
    request.session["state"] = state
    query = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "user-modify-playback-state user-read-playback-state",
        
    }
    url = URL(SPOTIFY_AUTH_URL).include_query_params(**query)
    return JSONResponse(
        {"error": "No token found. Please login first.", "url": str(url)}, status_code=401
    )

@auth.get("/callback")
async def callback(request: Request, state: str = Query(default=""), code: str | None = Query(default=None), error: str | None = Query(default=None)):
    await load_session(request)
    if state != request.session.get("state", ""):
        return Response({"error": "State does not match"}, status_code=401)
    if error is not None:
        return Response({"error": error}, status_code=401)
    if code is None:
        return Response({"error": "Spotify died. Got no error or code"}, status_code=500)
    redirect_uri = request.url_for("callback")
    redirect_uri = redirect_uri.replace(scheme=SCHEME)
    regenerate_session_id(request)
    request.session["state"] = None
    
    UserToken(code, redirect_uri)


    return HTMLResponse("""
<html><head><title>Spotify Auth</title></head>
<body>
<script>
window.close();
</script>
</body>
</html>
                        """)
