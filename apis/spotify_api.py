from flask import Flask, request, redirect, session, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from config import Config
from spotipy.cache_handler import FlaskSessionCacheHandler

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri=redirect_uri,
    scope=spotify_scope,

    cache_handler=cache_handler,
    show_dialog=True
) #This is the authentication manager, essentially how we will authenticate with the Spotify webAPI
sp = Spotify(auth_manager=sp_oauth)