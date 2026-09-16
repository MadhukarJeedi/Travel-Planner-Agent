import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

RAILRADAR_API_KEY = os.getenv("RAILRADAR_API_KEY")

BASE_URL = "https://api.railradar.in/v1"

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
    "bengaluru": "SBC",
    "mysore": "MYS",
    "mumbai": "CSTM",
    "delhi": "NDLS",
    "new delhi": "NDLS",
    "kolkata": "HWH",
    "howrah": "HWH",
    "pune": "PUNE",
    "goa": "MAO",
    "madgaon": "MAO",
    "ahmedabad": "ADI",
    "jaipur": "JP",
    "lucknow": "LKO",
    "bhopal": "BPL",
    "nagpur": "NGP",
    "coimbatore": "CBE",
    "kochi": "ERS",
    "ernakulam": "ERS",
    "trivandrum": "TVC",
    "thiruvananthapuram": "TVC",
    "patna": "PNBE",
    "bhubaneswar": "BBS",
    "guwahati": "GHY",
    "agra": "AGC",
    "varanasi": "BSB",
    "indore": "INDB",
    "surat": "ST",
    "raipur": "R",
}


def _get_station_train_numbers(station_code: str, headers: dict) -> dict:
    """
    Fetch all train numbers at a given station.
    Returns a dict of {train_number: entry} for quick lookup.
    """
    response = requests.get(
        f"{BASE_URL}/stations/{station_code}/trains",
        headers=headers,
        timeout=20,
    )
    if response.status_code != 200:
        return {}
    data = response.json()
    if not data.get("success"):
        return {}
    trains = data.get("data", {}).get("trains", [])
    return {entry["train"]["number"]: entry for entry in trains if "train" in entry}


@tool
def railway_tool(source: str, destination: str) -> str:
    """
    Find trains between two Indian cities or station codes using the RailRadar API.

    Examples:
    - Hyderabad to Goa
    - Secunderabad to Vijayawada
    - SC to WL
    """

    if not RAILRADAR_API_KEY:
        return "RailRadar API key not found. Please add RAILRADAR_API_KEY to your .env file."

    # Convert city names to station codes
    source_code = STATION_CODES.get(source.lower().strip(), source.upper().strip())
    destination_code = STATION_CODES.get(destination.lower().strip(), destination.upper().strip())

    headers = {
        "Authorization": f"Bearer {RAILRADAR_API_KEY}",
        "Accept": "application/json",
    }

    try:
        # Step 1: Get all trains at source station
        source_trains = _get_station_train_numbers(source_code, headers)
        if not source_trains:
            return f"Could not fetch trains from {source} ({source_code}). Please check the station code."

        # Step 2: Get all trains at destination station
        dest_trains = _get_station_train_numbers(destination_code, headers)
        if not dest_trains:
            return f"Could not fetch trains for {destination} ({destination_code}). Please check the station code."

        # Step 3: Find trains common to both stations (pass through both)
        common_numbers = set(source_trains.keys()) & set(dest_trains.keys())

        if not common_numbers:
            return (
                f"No direct trains found between {source} ({source_code}) "
                f"and {destination} ({destination_code})."
            )

        # Step 4: Format the matching trains (up to 5)
        trains_text = []
        for number in list(common_numbers)[:5]:
            entry = source_trains[number]
            train = entry.get("train", {})
            stop = entry.get("stop", {})  # Stop details at SOURCE station

            name = train.get("name", "Unknown Train")
            train_type = train.get("type", "")
            departure = stop.get("departure", "")
            run_days = train.get("runDays", [])

            days_str = f" | Days: {', '.join(run_days)}" if run_days else ""
            dep_str = f" | Departure: {departure}" if departure else ""
            type_str = f" ({train_type})" if train_type else ""

            trains_text.append(
                f"🚆 {name}{type_str} | Train No: {number}{dep_str}{days_str}"
            )

        result = (
            f"🚉 Trains from {source} ({source_code}) "
            f"to {destination} ({destination_code}):\n\n"
        )
        result += "\n".join(trains_text)
        return result

    except requests.exceptions.Timeout:
        return f"Request timed out while fetching trains from {source} to {destination}."
    except Exception as e:
        return f"Error fetching train information: {str(e)}"