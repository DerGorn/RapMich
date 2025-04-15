#!/usr/bin/env python3
"""
Module that makes use of the Spotify Web API to retrieve pseudo-random songs based
or not on a given exiting Spotify genre (look at genres.json, filled with info
scrapped from http://everynoise.com/everynoise1d.cgi?scope=all&vector=popularity)
Spotify Ref: https://developer.spotify.com/documentation/web-api/reference-beta/#category-search
"""

import base64
import json
import random
import requests
import sys
import timeit
from pydantic import BaseModel, AfterValidator
from typing import Annotated, List

from fuzzysearch import find_near_matches

def genre_validation(genre: List[str]) -> List[str]:
    try:
        with open('spotify_song_suggestion/genres.json', 'r') as infile:
            valid_genres = json.load(infile)
    except FileNotFoundError:
        raise ValueError("Couldn't find genres file!")
    if len(genre) == 0:
        raise ValueError("Empty genre list")
    validated_genres = []
    for g in genre:
        if g not in valid_genres:
            # If genre not found as it is, try fuzzy search with Levenhstein distance 2
            valid_genres_to_text = " ".join(valid_genres)
            try:
                closest_genre = find_near_matches(g, valid_genres_to_text,  max_l_dist=2)[0].matched
                validated_genres.append(closest_genre)
            except IndexError:
                raise ValueError(f"Invalid genre: {genre}")
        else:
            validated_genres.append(g)
    return validated_genres


class Genre(BaseModel):
    genre: Annotated[List[str], AfterValidator(genre_validation)]

# Spotify API URIs
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

class Token:
    token: str
    expiration: float
    refresh_token: str | None

    def __init__(self, token: str, expiration: float, refresh_token: str | None = None):
        self.token = token
        self.expiration = expiration
        self.refresh_token = refresh_token

token: Token | None = None

def get_token(client_id: str, client_secret: str, payload: dict, token: Token | None = None):
    if token is not None and timeit.default_timer() < (token.expiration - 2):
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

class SongInfo:
    uri: str
    name: str
    artist: str
    album: str
    release_date: str
    url: str
    
    def __init__(self, spotify_json: dict):
        self.uri = spotify_json["uri"]
        self.name = spotify_json["name"]
        self.artist = [x["name"] for x in spotify_json["artists"]]
        self.album = spotify_json["album"]["name"]
        self.release_date = spotify_json["album"]["release_date"]
        self.url = spotify_json["external_urls"]["spotify"]
    
    def __str__(self):
        return f"'{self.name}' by '{self.artist}' on '{self.album} ({self.release_date})'\n{self.url}"
    
    def to_json(self):
        return {
            "uri": self.uri,
            "name": self.name,
            "artist": self.artist,
            "album": self.album,
            "release_date": self.release_date,
            "url": self.url
        }

def request_valid_song(access_token, genre: str=None) -> SongInfo:
    # Wildcards for random search
    random_wildcards = [
        "%25a%25",
        "a%25",
        "%25a",
        "%25e%25",
        "e%25",
        "%25e",
        "%25i%25",
        "i%25",
        "%25i",
        "%25o%25",
        "o%25",
        "%25o",
        "%25u%25",
        "u%25",
        "%25u",
    ]
    wildcard = random.choice(random_wildcards)

    # Make a request for the Search API with pattern and random index
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Cap the max number of requests until getting RICK ASTLEYED
    for i in range(51):
        try:
            song_request = requests.get(
                "{}/search?q={}{}&type=track&offset={}".format(
                    SPOTIFY_API_URL,
                    wildcard,
                    "%20genre:%22{}%22".format(genre.replace(" ", "%20")),
                    random.randint(0, 1000),
                ),
                headers=authorization_header,
            )
            song_info = random.choice(json.loads(song_request.text)["tracks"]["items"])
            break
        except IndexError:
            continue

    
    return SongInfo(song_info)


def main(client_id: str, client_secret: str, genre: Genre | None = None):
    global token
    # Open genres file
    if genre is None:
        try:
            with open("spotify_song_suggestion/genres.json", "r") as infile:
                valid_genres = json.load(infile)
        except FileNotFoundError:
            print("Couldn't find genres file!")
            sys.exit(1)
    else:
        valid_genres = genre.genre

    selected_genre = random.choice(valid_genres)

    # Get a Spotify API token
    token = get_token(client_id, client_secret, {"grant_type": "client_credentials"}, token)
    # Call the API for a song that matches the criteria
    result = request_valid_song(token.token, genre=selected_genre)
    return result


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    song_info = main(os.environ.get("CLIENT_ID"), os.environ.get("CLIENT_SECRET"), Genre.model_validate_json('{"genre": ["black metal", "pop"]}'))
    print(song_info)
