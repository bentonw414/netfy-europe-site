# This file basically pulls mapbox images from the webapi
# https://docs.mapbox.com/api/maps/static-images/
from cmath import inf
from threading import local
from classes import SwarmCheckinData
from cleaning_swarm_checkins import clean_swarm_data
from pathlib import Path
import urllib.request

def get_mapbox_api_key():
    # put the api key in a file called "mapbox_api_key.txt"
    with open("./mapbox_api_key.txt", "r") as f:
        return f.read()

def correct_coordinate(coordinate: float):
    """
    """
    if coordinate > 90:
        return coordinate - 90
    if coordinate < -90:
        return coordinate + 90
    return coordinate

def get_request_url_from_coords(locations, max_latitude: float, max_longitude: float,
                                min_latitude: float, min_longitude: float, 
                                mapbox_api_key: str) -> str:
    """
    Edit the options in here to modify the image that the mapbox url returns
    """
    max_delta_total = max(max_latitude - min_latitude, max_longitude - min_longitude, .001)
    api_max_latitude = max_latitude/2 + min_latitude/2 + max_delta_total/2
    api_max_longitude = max_longitude/2 + min_longitude/2 + max_delta_total/2
    api_min_latitude = max_latitude/2 + min_latitude/2 - max_delta_total/2
    api_min_longitude = max_longitude/2 + min_longitude/2 - max_delta_total/2

    api_max_latitude = correct_coordinate(api_max_latitude)
    api_max_longitude = correct_coordinate(api_max_longitude)
    api_min_latitude = correct_coordinate(api_min_latitude)
    api_min_longitude = correct_coordinate(api_min_longitude)

    pixels_x = 1000
    pixels_y = 1000

    locations_string = ""
    for lat, lon in locations:
        locations_string += f"pin-s+555555({lon},{lat}),"

    if locations_string != "":
        locations_string = locations_string[:-1] + "/" # remove the comma

    style_id = "streets-v11"

    return f'https://api.mapbox.com/styles/v1/mapbox/{style_id}/static/{locations_string}[{api_min_longitude},{api_min_latitude},{api_max_longitude},{api_max_latitude}]/{pixels_x}x{pixels_y}?access_token={mapbox_api_key}'

def generate_images(output_folder_path: str, swarm_data: SwarmCheckinData) -> None:
    """
    Outputs a list of images, of the form "mapbox-<date of data>.png into the folder given
    by [output_folder_path]
    """
    folder_path = Path(output_folder_path)
    if not folder_path.exists():
        folder_path.mkdir()
    
    mapbox_api_key = get_mapbox_api_key()

    count = 0
    for date, date_checkins in swarm_data.checkin_data.items():
        max_latitude = -inf
        max_longitude = -inf
        min_latitude = inf
        min_longitude = inf
        locations = []
        for checkin in date_checkins:
            latitude = checkin['latitude']
            longitude = checkin['longitude']
            locations.append([latitude, longitude])
            max_latitude = max(latitude, max_latitude)
            max_longitude = max(longitude, max_longitude)
            min_latitude = min(latitude, min_latitude)
            min_longitude = min(longitude, min_longitude)
        
        api_call_url = get_request_url_from_coords(
            locations=[[max_latitude, max_longitude], [max_latitude, min_longitude], [min_latitude, max_longitude], [min_latitude, min_longitude]],
            max_latitude=max_latitude,
            max_longitude=max_longitude,
            min_latitude=min_latitude,
            min_longitude=min_longitude,
            mapbox_api_key=mapbox_api_key)


        if date == "2022-08-15":
            print(api_call_url)
            urllib.request.urlretrieve(api_call_url, folder_path.joinpath(f'mapbox-{date}.png'))
        
        count += 1
        if count >= inf:
            break

if __name__ == "__main__":
    generate_images(output_folder_path="./static/mapbox", swarm_data=SwarmCheckinData(clean_swarm_data()))
        
