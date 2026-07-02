import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

API_KEY = os.getenv("GEOAPIFY_API_KEY")


def get_city_coords(city: str):
    """
    Convert city name to latitude and longitude using Geoapify Geocoding API.
    """

    url = "https://api.geoapify.com/v1/geocode/search"

    params = {
        "text": city,
        "limit": 1,
        "apiKey": API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    features = data.get("features", [])

    if not features:
        return None

    lon, lat = features[0]["geometry"]["coordinates"]

    return lon, lat


@tool
def places_tool(city: str) -> str:
    """
    Get top tourist attractions in a city.
    """

    coords = get_city_coords(city)

    if not coords:
        return f"Could not find location information for {city}"

    lon, lat = coords

    url = "https://api.geoapify.com/v2/places"

    params = {
        "categories": "tourism.attraction",
        "filter": f"circle:{lon},{lat},10000",
        "limit": 10,
        "apiKey": API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return f"Error fetching attractions: {response.text}"

    data = response.json()

    attractions = []

    for place in data.get("features", []):
        properties = place.get("properties", {})

        name = properties.get("name")

        if name and name not in attractions:
            attractions.append(name)

    if not attractions:
        return f"No tourist attractions found in {city}"

    result = f"Top tourist attractions in {city}:\n\n"

    for i, attraction in enumerate(attractions, start=1):
        result += f"{i}. {attraction}\n"

    return result