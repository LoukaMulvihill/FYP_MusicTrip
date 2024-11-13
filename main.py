#This whole thing will read your spotify account and return a list of all your playlists
#Most code here is from https://www.youtube.com/watch?v=2if5xSaZJlg

import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, redirect, session, url_for
from config.config import Config
from apis.spotify_api import spotify_blueprint

app = Flask(__name__) #Creates the flask app and stores it in the app variable
app.config['SECRET_KEY'] = Config.SECRET_KEY #This creates a secret encryption key for flask to access the session data

# Register the Spotify API blueprint
app.register_blueprint(spotify_blueprint, url_prefix='/spotify')

if __name__ == '__main__pyth': #Tells python that when we run the app, everything in this block is run first
    app.run(debug=True) #The debug flag means that when changes are made in the code, the server is restarted so we dont have to do it manually
