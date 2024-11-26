from geopy.geocoders import Nominatim

def get_location(latitude, longitude):
    geolocator = Nominatim(user_agent="Register_bot")
    location = geolocator.reverse(f"{latitude}, {longitude}")

    return location