from email.mime import image
import os
from typing import Dict, List
import requests
import json
import datetime

def get_smugmug_api_key() -> str:
    if os.environ.get('APP_LOCATION') == "netlify":
        with open("./smugmug_api_key.txt", "w") as smugmug_api_key_f:
            smugmug_api_key_f.write(os.environ.get("SMUGMUG_API_KEY"))
    
    with open("./smugmug_api_key.txt", "r") as smugmug_api_key_f:
        return smugmug_api_key_f.read()
    


def get_smugmug_data():
    """
    Returns a json for all pictures from the trip by making smugmug api request
    """
    # all the pictures from the europe trip
    url = "https://www.smugmug.com/api/v2/album/CnMdTP!images?count=10000"

    params = {
        "count": 10000,
        "APIKey": get_smugmug_api_key(),
        "ShowKeywords": True,
    }
    headers = {'Accept': 'application/json'}

    resp = requests.get(url=url, params=params, headers=headers)
    data = resp.json()

    data = json_reformatting(data)
    return data


def get_json_at_file(json_file_path):
    with open(json_file_path) as f:
        return json.load(f)


def json_reformatting(json: Dict):
    """
    Returns a few new json style dictionaries:
    One contains only the favorites:
        Maps Date ==> List[ImageKey]
    The other contains all the images:
        Maps Date ==> List[ImageKey]
    The last one contains the data and is of the form:
    ImageKey => {
        "largest_uri": "URI",
        "thumbnail_uri: something,
        "keywords": List[keyword strings],
        "caption": "some caption",
        "title": "some Title"
    }
    """

    date_overrides = get_json_at_file("./site_building_data/image_date_overrides.json")

    # TODO favs and keywords once they are working
    favs_out = {}
    all_out = {}
    key_to_metadata = {}
    count_without_date = 0
    for image_data in json["Response"]["AlbumImage"]:
        title = image_data["Title"]
        # 2022-07-11T13:50:19+00:00 should be 
        date_format_parse = "%Y-%m-%dT%H:%M:%S"
        # the :10 is to strip the more accurate part of the time
        image_key = image_data["ImageKey"]
        caption = image_data["Caption"]
        largest_uri = image_data["ArchivedUri"]
        thumbnail_uri = image_data["ThumbnailUrl"]
        largewidth = image_data["OriginalWidth"]
        largeheight = image_data["OriginalHeight"]

        if image_key in date_overrides:
            date = date_overrides[image_key]
        else:
            datestr = image_data["DateTimeOriginal"][:-6]
            parsed_date = datetime.datetime.strptime(datestr, date_format_parse)
            # shift the pictures to be accurately dated (by 7 hours)
            shifted_date = (parsed_date - datetime.timedelta(hours=7)).date()
            date = datetime.datetime.strftime(shifted_date, "%Y-%m-%d")

        if date not in all_out:
            all_out[date] = [image_key]
        else:
            all_out[date].append(image_key)
        
        key_to_metadata[image_key] = {
            "largest_uri" : largest_uri,
            "title" : title,
            "caption" : caption,
            "thumbnail_uri" : thumbnail_uri,
            "largewidth" : str(largewidth),
            "largeheight" : str(largeheight),
        }
    print("count without date: ", count_without_date)
    return favs_out, all_out, key_to_metadata

if __name__ == "__main__":
    get_smugmug_data()