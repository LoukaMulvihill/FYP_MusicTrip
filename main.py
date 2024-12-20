#This whole thing will read your spotify account and return a list of all your playlists
#Most code here is from https://www.youtube.com/watch?v=2if5xSaZJlg

import os
from flask import Flask, request, redirect, session, url_for, render_template #Imports flask library. Also imports the session. The session is the instance of the server that will store data while the user is using the app
from API import setup_spotify_auth, search_ticketmaster_events, get_return_route

app = Flask(__name__) #Creates the flask app and stores it in the app variable
app.config['SECRET_KEY'] = os.urandom(64) #This creates a secret encryption key for flask to access the session data

sp, sp_oauth, cache_handler = setup_spotify_auth(session)

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
    playlist_id = request.args.get('playlist_id')
    if not playlist_id:
        return "No playlist ID provided", 400
    
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    try:
        playlist_data = sp.playlist_tracks(playlist_id)
    except Exception as e:
        return f"Error fetching playlist tracks: {e}", 400
    
    # Gather unique artists
    artists = []
    for item in playlist_data['items']:
        track = item['track']
        track_artists = [artist['name'] for artist in track['artists']]
        artists.extend(track_artists)
    
    unique_artists = sorted(set(artists))
    
    # Separate artists with and without events
    artists_with_events = []
    artists_without_events = []
    ticketmaster_events = []

    for artist in unique_artists:
        events = search_ticketmaster_events(artist)
        if events:
            # Add to artists with events
            artists_with_events.append((artist, events))
            # Generate HTML for the artist with events
            event_html = "".join([
                f"""
                <li>
                    <strong>{event['name']}</strong><br>
                    Date: {event['date']}<br>
                    Venue: {event['venue']}, {event['city']}, {event['country']}<br>
                    Price: {event['price']}<br>
                    <a href="{event['url']}" target="_blank">Buy Tickets</a>
                </li>
                """ for event in events
            ])
            ticketmaster_events.append(f"<h4>{artist}</h4><ul>{event_html}</ul>")
        else:
            # Add to artists without events
            artists_without_events.append(artist)
            ticketmaster_events.append(f"<h4>{artist}</h4><p>No concert data available.</p>")
    
    # Sort the lists alphabetically
    artists_with_events.sort(key=lambda x: x[0])
    artists_without_events.sort()
    
    # Generate the dropdown menu
    dropdown_menu = "".join([f'<option value="{artist}">{artist}</option>' for artist in artists_with_events + artists_without_events])
    
     # Generate HTML for Ticketmaster results
    ticketmaster_html_with_events = "".join([
        f"""
        <h4>{artist}</h4>
        <ul>
            {''.join([
                f"""
                <li>
                    <strong>{event['name']}</strong><br>
                    Date: {event['date']}<br>
                    Venue: {event['venue']}, {event['city']}, {event['country']}<br>
                    Price: {event['price']}<br>
                    <a href="{event['url']}" target="_blank">Buy Tickets</a><br>
                    <form action="/find_return_route" method="post" style="display:inline;">
                        <input type="hidden" name="event_date" value="{event['date']}">
                        <input type="hidden" name="event_city" value="{event['city']}">
                        <input type="hidden" name="event_country" value="{event['country']}">
                        <input type="hidden" name="event_venue" value="{event['venue']}">
                        <button type="submit">Find Travel Options</button>
                    </form>
                </li>
            """ for event in events
            ])}
        </ul>
        """ for artist, events in artists_with_events
    ])

    ticketmaster_html_without_events = "".join([
        f"<h4>{artist}</h4><p>No concert data available.</p>"
        for artist in artists_without_events
    ])

    # Combine the HTML for Ticketmaster results
    ticketmaster_html = ticketmaster_html_with_events + ticketmaster_html_without_events
    
    # Generate the dropdown menu
    dropdown_menu = "".join([f'<option value="{artist}">{artist}</option>' for artist in unique_artists])

    try: #retrieves the playlist name from playlist_details to display the playlist name at the top of the page instead of playlist ID
        playlist_details = sp.playlist(playlist_id) 
        playlist_name = playlist_details['name']
    except Exception as e:
        playlist_name = "Unknown Playlist"

    # Return the final HTML
    return f"""
        <h3>Artists in Playlist: {playlist_name}</h3>
        <div>
            <select>
                <option value="" disabled selected>View list of artists</option>
                {dropdown_menu}
            </select>
        </div>
        <div style="display: flex; justify-content: space-between; width: 100%; height: 100vh;">
            <div style="border: 1px solid #ccc; padding: 15px; width: 33%; height: 100vh; overflow-y: auto;">
                <h3>Ticketmaster Results</h3>
                {ticketmaster_html}
            </div>
        </div>
    """

#future travel and accommodation call
@app.route('/find_return_route', methods=['POST'])
def find_return_route():
    #Get event details from the form
    event_date = request.form.get('event_date')
    event_city = request.form.get('event_city')
    event_country = request.form.get('event_country')
    event_venue = request.form.get('event_venue')

    #combine address
    event_location = f"{event_venue}, {event_city}, {event_country}"

    # Pass data to the frontend
    return render_template(
        'map.html',
        source_address="26 ard na gréine, Dingle, County Kerry",  # Default source
        destination_address=event_location,
    )


    #Call travel API
  #  route = get_return_route(event_location, event_date)
#
 #   if not route:
  #      return "Could not find a route", 400
    
    #new page with route details
   # return f"""
    #    <h3>Travel Options</h3>
     #   <h4>To Event:</h4>
     #   <p>Duration: {route['to_event']['duration']}</p>
    #    <p>Distance: {route['to_event']['distance']}</p>
    #    <ol>{"".join(f"<li>{step}</li>" for step in route['to_event']['steps'])}</ol>

#        <h4>Return Trip:</h4>
 #       <p>Duration: {route['to_source']['duration']}</p>
  #      <p>Distance: {route['to_source']['distance']}</p>
   #     <ol>{"".join(f"<li>{step}</li>" for step in route['to_source']['steps'])}</ol>

    #    <a href="/">Go Back</a>
    #"""


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home')) #allows to user to logout, removing the access token and forcing the user to login again

if __name__ == '__main__': #Tells python that when we run the app, everything in this block is run first
    app.run(debug=True) #The debug flag means that when changes are made in the code, the server is restarted so we dont have to do it manually
