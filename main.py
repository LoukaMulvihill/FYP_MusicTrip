#This whole thing will read your spotify account and return a list of all your playlists
#Most code here is from https://www.youtube.com/watch?v=2if5xSaZJlg
import os

from flask import Flask, request, redirect, session, url_for #Imports flask library. Also imports the session. The session is the instance of the server that will store data while the user is using the app

from spotipy import Spotify #These three are imports to set up authorisation
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__) #Creates the flask app and stores it in the app variable
app.config['SECRET_KEY'] = os.urandom(64) #This creates a secret encryption key for flask to access the session data

client_id = 'fea86757afda461180f61c4493680c53'#client_id, client_secret and redirect_uri are gotten from my Spotify API developer account
client_secret = 'a78a01726ac3424d99c057ce1df15913'
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private'#This was gotten from a list of available scopes on the Spotify Documentation webpage, this specific scope gives access to read the users private playlists

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
) #This is the authentication manager, essentially how we will authenticate with the Spotify webAPI
sp = Spotify(auth_manager=sp_oauth)

@app.route('/') #"app"=the flask app, "route" is how you define your route for a webapp in flaask and '/' is the route.
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()): #sp_oauth has a function that allows to check for valid tokens and one to retrieve a cached token from the session
        auth_url = sp_oauth.get_authorize_url() #Basically, this "if not" function handles the scenario where a user hasnt previously logged in to their spotify account and we want to bring them to the spotify login page
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists')) #This piece of code allows the authentication manager to store a 'code' which it will use to get the access token going forward. This means the user won't have to constantly log in to their Spotify when they want to use the app.

@app.route('/get_playlists')
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()): #Copy and pasted code from above, checking if the token is valid
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    playlists = sp.current_user_playlists()
    playlists_info = [(pl['name'], pl['id']) for pl in playlists['items']]
    #playlists_html = '<br>'.join([f'{name}: (ID: {playlist_id})' for name, playlist_id in playlists_info]) # this prints out the name, url and id of the playlists. Easier to read
    playlists_html = ''.join([
        f'<form action="/playlist_tracks" method="get" style="margin-bottom: 10px;">'
        f'<input type="hidden" name="playlist_id" value="{playlist_id}">'
        f'<button type="submit">{name}</button>'
        f'</form>'
        for name, playlist_id in playlists_info
    ])

    return f"<h3> Your Playlists</h3>{playlists_html}"

@app.route('/playlist_tracks')
def playlist_tracks():
    playlist_id = request.args.get('playlist_id')  #Get the 'playlist_id' from the URL
    if not playlist_id:
        return "No playlist ID provided", 400   #If 'playlist_id' is missing, return an error
    
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    try:
        playlist_data = sp.playlist_tracks(playlist_id)
    except Exception as e:
        return f"Error fetching playlist tracks: {e}", 400
    
    artists = []                                                           # CHATGPT   Initializes an empty list, artists
    for item in playlist_data[ 'items']:                                   # CHATGPT   Loops through each item in the 'items' list from 'playlist_data' which represents tracks
        track = item['track']                                              # CHATGPT   Extracts the 'track' dictionary from each item, which contains info about the track
        track_artists = [artists['name'] for artists in track ['artists']] # CHATGPT   Extracts the names of the artists for each track and stores them in a list, track_artists. Each 'track['artists']' entry is an artists involved in a  track
        artists.extend(track_artists)                                      # CHATGPT   Extends the artists list with the names of the artists in track_artists
                                                                           # CHATGPT
    unique_artists = set(artists)                                          # CHATGPT   Convert 'artists' to a det, 'unique_artists', as sets do not allow duplicate entries
    artists_html = '<br>'.join(unique_artists)                             # CHATGPT   HTML formatting

    return f"<h3> Artists in Playlist (ID: {playlist_id}):</h3><br>{artists_html}" 

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home')) #allows to user to logout, removing the access token and forcing the user to login again

if __name__ == '__main__': #Tells python that when we run the app, everything in this block is run first
    app.run(debug=True) #The debug flag means that when changes are made in the code, the server is restarted so we dont have to do it manually
