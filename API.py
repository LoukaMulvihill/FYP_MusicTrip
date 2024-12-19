import os
import requests
from spotipy import Spotify #These three are imports to set up authorisation
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

spotify_client_id = 'fea86757afda461180f61c4493680c53'#client_id, client_secret and redirect_uri are gotten from my Spotify API developer account
spotify_client_secret = 'a78a01726ac3424d99c057ce1df15913'
redirect_uri = 'http://localhost:5000/callback'
spotify_scope = 'playlist-read-private'#This was gotten from a list of available scopes on the Spotify Documentation webpage, this specific scope gives access to read the users private playlists
ticketmaster_consumer_key = '8kN3GmP1POuzUiGv2LrzBByA9dPGuom2'
ticketmaster_consumer_secret = '6ZEAtoBunKhyZmZa'

def setup_spotify_auth(session):
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
    return sp, sp_oauth, cache_handler

def search_ticketmaster_events(artist_name): #Function to search for events in ticketmaster based on artist name
    """Search for upcoming events on Ticketmaster for a given artist name."""
    url = 'https://app.ticketmaster.com/discovery/v2/events'
    params = {
        'apikey': ticketmaster_consumer_key,
        'keyword': artist_name,
        'classificationName': 'music',
        'size': 20
    }

    response = requests.get(url, params=params)
    events = []
    if response.status_code == 200:
        data = response.json()
        if '_embedded' in data and 'events' in data['_embedded']: #checks if there are any events in the response
            for event in data['_embedded']['events']:
                # Safely retrieve event details
                event_name = event.get('name', 'Event name not available')
                event_date = event['dates']['start'].get('localDate', 'Date not available')

                # Venue details
                venue_name = 'Venue not available'
                city = 'City not available'
                country = 'Country not available'
                if '_embedded' in event and 'venues' in event['_embedded']:
                    venue = event['_embedded']['venues'][0]
                    venue_name = venue.get('name', 'Venue name not available')
                    city = venue.get('city', {}).get('name', 'City not available')
                    country = venue.get('country', {}).get('name', 'Country not available')

                # Price range
                price_range = 'Price not available'
                if 'priceRanges' in event:
                    prices = event['priceRanges'][0]
                    min_price = prices.get('min', 'N/A')
                    max_price = prices.get('max', 'N/A')
                    currency = prices.get('currency', '')
                    price_range = f"{min_price} - {max_price} {currency}"

                # Ticketmaster URL
                ticket_url = event.get('url', '#')

                # Add event information to the list
                event_info = {
                    'name': event_name,
                    'date': event_date,
                    'venue': venue_name,
                    'city': city,
                    'country': country,
                    'price': price_range,
                    'url': ticket_url
                }
                events.append(event_info)
        else:
            print(f"No events found for {artist_name}. Response: {response.json()}")
    else:
        print(f"Ticketmaster API request failed for artist {artist_name} with status code {response.status_code}")

    return events