import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool
load_dotenv()

API_KEY = os.getenv("ORS_API_KEY")

#Route tool
@tool 
def route_tool(start:str, end:str):
    "Calculate the distance between two cities."
    
    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    
    params = {"start":start,
              "end":end,
              "api_key":API_KEY}
    

    response = requests.get(url,params=params)

    data = response.json()
    # Error handling
    if response.status_code != 200:
        return f"Error fetching route: {data}"
    
    return f"Route information  {data}"
