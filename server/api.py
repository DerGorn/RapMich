from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi import Query
from typing import List
from spotify_song_suggestion.random_song import main as get_random_song, Genre, SongInfo
from pydantic import BaseModel
from starsessions import load_session
import random
import requests
from dotenv import load_dotenv
from auth import auth, ClientToken, UserToken
load_dotenv()

api = APIRouter(prefix="/api")

class Playlist(BaseModel):
    id: str
    tracks: List[SongInfo] = []
    index: int = 0 

    async def populate_playlist(self):
        limit = 100
        offset = 0
        print(f"Populating playlist {self.id}")
        while True:
            response = requests.get(
                f"https://api.spotify.com/v1/playlists/{self.id}/tracks?fields=items.track(name,uri,artists.name,album(name,release_date),external_urls.spotify)&limit={limit}&offset={offset}",
                headers={"Authorization": f"Bearer {ClientToken().token}"},
            )
            if response.status_code != 200:
                return JSONResponse(
                    {"error": "Failed to read Playlist", "details": response.json()["error"]}, status_code=response.status_code
                )
            tracks = response.json()["items"]
            if len(tracks) == 0:
                break
            for track in tracks:
                track_info = SongInfo(spotify_json=track["track"])
                self.tracks.append(track_info)
            offset += limit
            print(f"Read {offset} tracks so far")
        random.shuffle(self.tracks)
        self.index = random.randint(0, len(self.tracks) - 1)

    def get_song_info(self) -> SongInfo:
        if len(self.tracks) == 0:
            return None
        if self.index >= len(self.tracks):
            self.index = 0
        song_info = self.tracks[self.index]
        self.index += 1
        return song_info

class Playlists(BaseModel):
    playlists: dict[str, Playlist]


@api.get("/songinfo/playlist/{id}")
async def random_from_playlist(request: Request, id):
    await load_session(request)
    print("START", request.session.get("playlists"))
    playlists = Playlists.model_validate_json(request.session.get("playlists", '{"playlists": {}}'))
    if id not in playlists.playlists:
        playlists.playlists[id] = Playlist(id=id)
        if error := await playlists.playlists[id].populate_playlist():
            return error
    print(f"Playlist {id} has {len(playlists.playlists[id].tracks)} songs")
    song_info = playlists.playlists[id].get_song_info().to_json()
    request.session["playlists"] = playlists.model_dump_json()
    print("END", request.session.get("playlists"))
    return JSONResponse(song_info)
        
@api.get("/songinfo/genre")
async def random_from_genre(genres: List[str] | None = Query(default=None)):
    # genre = ["german hip hop", "rock and roll", "german trap", "german hip hop", "german pop rock", "groove metal", "nu metal", "german pop"]
    # genre = ["german hip hop", "metalcore", "drum and bass", "death metal", "german trap"]
    if genres:
        inner = '{"genre": ['
        first = True
        for g in genres:
            if not first:
                inner += ", "
            inner += f'"{g}"'
            first = False
        inner += "]}"
        genre = Genre.model_validate_json(inner)
    song_info = get_random_song(ClientToken(), genre) 
    return JSONResponse(song_info.to_json())
    

@api.post("/play")
async def play(uri: str):
    try:
        token = UserToken()
    except ValueError:
        return RedirectResponse(url=auth.url_path_for("login"), status_code=302)

    response = requests.get(
        "https://api.spotify.com/v1/me/player/devices",
        headers={"Authorization": f"Bearer {token.token}"},
    )
    if response.status_code != 200:
        return JSONResponse(
            {"error": "Failed to get devices", "details": response.json()["error"]}, status_code=response.status_code
        )
    devices = response.json()["devices"]
    device_id = None
    for device in devices:
        if device["is_active"]:
            device_id = device["id"]
            break
    if device_id is None:
        device_id = devices[0]["id"] if devices else None

    body = {
        "uris": [uri],
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
    return Response(status_code=204)

