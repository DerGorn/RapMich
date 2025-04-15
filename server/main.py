from fastapi import FastAPI, APIRouter
from fastapi.datastructures import URL
from fastapi.responses import RedirectResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from typing import List
from spotify_song_suggestion.random_song import main as get_random_song, Genre, get_token, Token
import sys
import os
import random
import requests
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Client Keys
CLIENT_ID = os.environ.get("CLIENT_ID", None)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", None)

if CLIENT_ID is None or CLIENT_SECRET is None:
    print(
        "Please set CLIENT_ID and CLIENT_SECRET environment variables to authenticate your app with spotify."
    )
    sys.exit(1)

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'

@app.get("/random")
async def random_song(genre: List[str] | None = Query(default=None)):
    genre = ["german hip hop"]
    if token is None:
        return RedirectResponse(url=auth.url_path_for("login"))
    if genre:
        inner = '{"genre": ['
        first = True
        for g in genre:
            if not first:
                inner += ", "
                first = False
            inner += f'"{g}"'
        inner += "]}"
        genre = Genre.model_validate_json(inner)
    print(genre)
    song_info = get_random_song(CLIENT_ID, CLIENT_SECRET, genre) 

    response = requests.get(
        "https://api.spotify.com/v1/me/player/devices",
        headers={"Authorization": f"Bearer {token.token}"},
    )
    if response.status_code != 200:
        return JSONResponse(
            {"error": "Failed to get devices", "details": response.json()["error"]}, status_code=response.status_code
        )
    devices = response.json()["devices"]
    print("deviced", devices)
    device_id = None
    for device in devices:
        if device["is_active"]:
            device_id = device["id"]
            break
    if device_id is None:
        device_id = devices[0]["id"] if devices else None
    print("device_id", device_id)

    body = {
        "uris": [song_info.uri],
    }
    response = requests.put(
        "https://api.spotify.com/v1/me/player/play" + (("?device_id=" + device_id) if device_id else ""),
        headers={"Authorization": f"Bearer {token.token}"},
        json=body,
    )
    if response.status_code != 204:
        return JSONResponse(
            {"error": "Failed to start playback", "details": response.json()["error"]}, status_code=response.status_code
        )
    print(song_info)
    return song_info.to_json()

auth = APIRouter(prefix="/auth")

token: Token | None = None

def random_string(len: int) -> str:
    symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    string = ""
    for i in range(len):
        string + random.choice(symbols)
    return string

@auth.get("/login")
async def login():
    query = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": random_string(32),
        "scope": "user-modify-playback-state user-read-playback-state",
        
    }
    url = URL(SPOTIFY_AUTH_URL).include_query_params(**query)
    return JSONResponse(
        {"error": "No token found. Please login first.", "url": str(url)}, status_code=401
    )

@auth.get("/callback")
async def callback(state: str = Query(default=""), code: str | None = Query(default=None), error: str | None = Query(default=None)):
    global token
    if error is not None:
        return Response({"error": error}, status_code=401)
    if code is None:
        return Response({"error": "Spotify died. Got no error or code"}, status_code=500)
    
    token_request_body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    token = get_token(CLIENT_ID, CLIENT_SECRET, token_request_body, token=token)



app.include_router(auth)
REDIRECT_URI = "http://127.0.0.1:8000" + app.url_path_for("callback")    
