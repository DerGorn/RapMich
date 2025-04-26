#!/usr/bin/env python3
"""
Module that makes use of the Spotify Web API to retrieve pseudo-random songs based
or not on a given exiting Spotify genre (look at genres.json, filled with info
scrapped from http://everynoise.com/everynoise1d.cgi?scope=all&vector=popularity)
Spotify Ref: https://developer.spotify.com/documentation/web-api/reference-beta/#category-search
"""

import json
import random
import requests
import sys
from auth import Token
from pydantic import BaseModel, AfterValidator, model_validator
from typing import Annotated, List, Any

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
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

class SongInfo(BaseModel):
    uri: str
    name: str
    artist: List[str]
    album: str
    release_date: str
    url: str

    @model_validator(mode="before")
    @classmethod   
    def destructure_spotify_json(self, data: Any):
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON format. Expected spotify JSON as dict.")
        if "spotify_json" in data:
            spotify_json = data["spotify_json"]
        elif "uri" in data and "artist" in data:
            # Desereliazation of allready validated Songinfo
            return data
        else:
            raise ValueError("Invalid JSON format. Expected spotify JSON as dict.")
        data = {}
        data["uri"] = spotify_json["uri"]
        data["name"] = spotify_json["name"]
        data["artist"] = [x["name"] for x in spotify_json["artists"]]
        data["album"] = spotify_json["album"]["name"]
        data["release_date"] = spotify_json["album"]["release_date"]
        data["url"] = spotify_json["external_urls"]["spotify"]
        return data
    
    def __repr__(self):
        return str(self)
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
                    random.randint(0, 400),
                ),
                headers=authorization_header,
            )
            song_info = random.choice(json.loads(song_request.text)["tracks"]["items"])
            break
        except IndexError:
            continue

    
    return SongInfo(song_info)


def main(token: Token, genre: Genre | None = None):
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
    print(selected_genre)

    # Call the API for a song that matches the criteria
    result = request_valid_song(token.token, genre=selected_genre)
    return result
