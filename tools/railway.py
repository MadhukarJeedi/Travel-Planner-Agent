import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

RAPID_KEY = os.getenv("RAPIDAPI_KEY")

# City -> Station Code Mapping
STATION_CODES = {
    "hyderabad": "SC",
    "secunderabad": "SC",
    "warangal": "WL",
    "vijayawada": "BZA",
    "tirupati": "TPTY",
    "chennai": "MAS",
    "visakhapatnam": "VSKP",
    "bangalore": "SBC",
    "mysore": "MYS",
    "mumbai": "CSTM",
    "delhi": "NDLS",
    "kolkata": "HWH",
    "pune": "PUNE",
    "goa": "MAO"
}


@tool
def railway_tool(source: str, destination: str) -> str:
    """
    Find trains between two Indian cities or station codes.

    Examples:
    - Hyderabad to Warangal
    - Secunderabad to Vijayawada
    - SC to WL
    """

    if not RAPID_KEY:
        return "RapidAPI key not found. Please check your .env file."

    # Convert city names to station codes
    source_code = STATION_CODES.get(
        source.lower(),
        source.upper()
    )

    destination_code = STATION_CODES.get(
        destination.lower(),
        destination.upper()
    )

    url = "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"

    querystring = {
        "fromStationCode": source_code,
        "toStationCode": destination_code
    }

    headers = {
        "X-RapidAPI-Key": RAPID_KEY,
        "X-RapidAPI-Host": "irctc1.p.rapidapi.com"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=querystring,
            timeout=20
        )

        print("Status Code:", response.status_code)
        print("Response:", response.text)

        if response.status_code != 200:
            return f"API Error ({response.status_code}): {response.text}"

        data = response.json()

        # Handle API errors
        if not data.get("status", False):
            return data.get(
                "message",
                "Unable to fetch train information."
            )

        trains = []

        for train in data.get("data", [])[:5]:

            train_name = train.get(
                "train_name",
                "Unknown Train"
            )

            train_number = train.get(
                "train_number",
                "N/A"
            )

            trains.append(
                f"🚆 {train_name} ({train_number})"
            )

        if not trains:
            return (
                f"No trains found between "
                f"{source} and {destination}"
            )

        result = (
            f"🚉 Trains from {source} to {destination}:\n\n"
        )

        result += "\n".join(trains)

        return result

    except Exception as e:
        return f"Error fetching train information: {str(e)}"