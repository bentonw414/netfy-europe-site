import json
from math import inf
from operator import index
from typing import Dict
import datetime

def get_json_data():
    with open("./site_building_data/swarm_checkins.json", "r") as f:
        return json.load(f)

def convert_epoch_time_to_datestring(epoch_time: int, offset: int) -> str:
    # TODO this is ignoring the timezone, but for the date I don't think it really should matter? Not really sure what the tz offet is doing
    # one thing that might correct it is using epoch_time - offset? but not really sure
    return datetime.datetime.fromtimestamp(epoch_time).date().strftime("%Y-%m-%d")


def clean_swarm_data() -> Dict:
    from make_mapbox_images import correct_coordinate
    """
    Returns the cleaned swarm data with the uppder level key being the date string in the format "%Y-%m-%d"
    """
    json_data = get_json_data()

    new_data: Dict = {}

    for single_checkin_data in json_data:
        single_new_data = {
            "venue_name" : single_checkin_data["venue"]["name"][0],
            "images": list(map(lambda single_image_data: {"prefix" : single_image_data['prefix'][0], "suffix" : single_image_data['suffix'][0]}, single_checkin_data['photos']['items'])),
            "latitude" : single_checkin_data["venue"]["location"]["lat"][0],
            "longitude" : single_checkin_data["venue"]["location"]["lng"][0],
            "venue_id" : single_checkin_data["venue"]["id"][0],
            "venue_url" : f'https://foursquare.com/v/{single_checkin_data["venue"]["id"][0]}',
            "epoch_time" : single_checkin_data['createdAt'][0]
        }

        epoch_time: int = single_checkin_data['createdAt'][0]
        timezone_offset: int = single_checkin_data['timeZoneOffset'][0]
        date_string = convert_epoch_time_to_datestring(epoch_time, timezone_offset)

        if date_string in new_data:
            new_data[date_string]['all'].append(single_new_data)
        else:
            new_data[date_string] = {'all' : [single_new_data]}

        for date, date_checkins in new_data.items():
            max_latitude = -inf
            max_longitude = -inf
            min_latitude = inf
            min_longitude = inf
            locations = []
            for checkin in date_checkins['all']:
                latitude = checkin['latitude']
                longitude = checkin['longitude']
                max_latitude = max(latitude, max_latitude)
                max_longitude = max(longitude, max_longitude)
                min_latitude = min(latitude, min_latitude)
                min_longitude = min(longitude, min_longitude)
        
            date_checkins['min_longitude'] = min_longitude
            date_checkins['max_longitude'] = max_longitude
            date_checkins['max_latitude'] = max_latitude
            date_checkins['min_latitude'] = min_latitude
            date_checkins['all'].sort(key=lambda x: x['epoch_time']) # should sort using the time


    
    return new_data
