from fastapi import APIRouter, Request
from fastapi.datastructures import URL
from fastapi.responses import Response, JSONResponse
from fastapi import Query
# from spotify_song_suggestion.random_song import main as get_random_song, Genre, get_token, Token, SongInfo
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
    query = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": request.url_for("callback"),
        "state": random_string(32),
        "scope": "user-modify-playback-state user-read-playback-state",
        
    }
    url = URL(SPOTIFY_AUTH_URL).include_query_params(**query)
    return JSONResponse(
        {"error": "No token found. Please login first.", "url": str(url)}, status_code=401
    )

@auth.get("/callback")
async def callback(request: Request, state: str = Query(default=""), code: str | None = Query(default=None), error: str | None = Query(default=None)):
    if error is not None:
        return Response({"error": error}, status_code=401)
    if code is None:
        return Response({"error": "Spotify died. Got no error or code"}, status_code=500)
    
    UserToken(code, request.url_for("callback"))
