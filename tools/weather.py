import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

#weather tools
@tool
def weather_tool(city:str):
    "Get the current weather for the given city"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)

    data =response.json()
    
     # Error handling
    if str(data.get("cod")) != "200":
        return f"Error fetching weather: {data}"
    
    description = data["weather"][0]["description"]
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    
    return (
        f"Weather in {city}:\n"
        f"Condition: {description}\n"
        f"Temperature: {temperature}°C\n"
        f"Humidity: {humidity}%"
    )