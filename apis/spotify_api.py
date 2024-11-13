from flask import Blueprint, request, redirect, session, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from config.config import Config
from spotipy.cache_handler import FlaskSessionCacheHandler

#class spotify_blueprint():
spotify_blueprint = Blueprint('spotify', __name__)
#print("spotify_blueprint type:", type(spotify_blueprint)) 
#print("spotify_blueprint attributes:", dir(spotify_blueprint))

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=Config.spotify_client_id,
    client_secret=Config.spotify_client_secret,
    redirect_uri=Config.redirect_uri,
    scope=Config.spotify_scope,
#    spotipy_redirect_uri = Config.spotipy_redirect_uri,
    cache_handler=cache_handler,
    show_dialog=True
) #This is the authentication manager, essentially how we will authenticate with the Spotify webAPI
sp = Spotify(auth_manager=sp_oauth)

@spotify_blueprint.route('/') #"app"=the flask app, "route" is how you define your route for a webapp in flaask and '/' is the route.
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()): #sp_oauth has a function that allows to check for valid tokens and one to retrieve a cached token from the session
        auth_url = sp_oauth.get_authorize_url() #Basically, this "if not" function handles the scenario where a user hasnt previously logged in to their spotify account and we want to bring them to the spotify login page
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))

@spotify_blueprint.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists')) #This piece of code allows the authentication manager to store a 'code' which it will use to get the access token going forward. This means the user won't have to constantly log in to their Spotify when they want to use the app.

@spotify_blueprint.route('/get_playlists')
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()): #Copy and pasted code from above, checking if the token is valid
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    playlists = sp.current_user_playlists()
    playlists_info = [(pl['name'], pl['id']) for pl in playlists['items']]
    playlists_html = ''.join([
        f'<form action="/playlist_tracks" method="get" style="margin-bottom: 10px;">'
        f'<input type="hidden" name="playlist_id" value="{playlist_id}">'
        f'<button type="submit">{name}</button>'
        f'</form>'
        for name, playlist_id in playlists_info
    ]) #Calls current_user_playlist from the spotify API. Gets 'name' and 'id' of each song. Creates a the layout with the 'name' as visible text and the 'id' as the idenitifer the system will use

    return f"<h3> Your Playlists</h3>{playlists_html}"

@spotify_blueprint.route('/playlist_tracks')
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
    
    artists = []                                                           # CHATGPT   makes an empty list called artists
    for item in playlist_data[ 'items']:                                   # CHATGPT   Loops through each item in the 'items' list from 'playlist_data' which represents tracks. 'Items' is an attribute given in the SpotifyAPI documentation
        track = item['track']                                              # CHATGPT   Extracts the 'track' dictionary from each item, which contains info about the track. 'Track' is an attribute given in the SpotifyAPI documentation
        track_artists = [artists['name'] for artists in track ['artists']] # CHATGPT   Extracts the names of the artists for each track and stores them in a list called track_artists. Each 'track['artists']' entry is an artists involved in a  track
        artists.extend(track_artists)                                      # CHATGPT   Extends the artists list with the names of the artists in track_artists
                                                                           # CHATGPT
    unique_artists = set(artists)                                          # CHATGPT   Convert 'artists' to a set, 'unique_artists', as sets do not allow duplicate entries
    artists_html = '<br>'.join(unique_artists)                             # CHATGPT   Formatting
    
    return f"<h3> Artists in Playlist (ID: {playlist_id}):</h3><br>{artists_html}" 

@spotify_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home')) #allows to user to logout, removing the access token and forcing the user to login again
