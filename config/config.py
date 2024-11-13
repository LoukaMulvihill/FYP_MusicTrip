# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    spotify_client_id = os.getenv('spotify_client_id')
    spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    firebase_url = os.getenv('FIREBASE_URL')
    redirect_uri = os.getenv('redirect_uri')
    spotify_scope = 'playlist-read-private'
#    spotipy_redirect_uri = os.getenv('spotipy_redirect_uri')
