"""
Weather Agent — Specialist agent powered by OpenWeather API.
Responsible ONLY for fetching current weather & forecast data.
"""

import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from tools.weather import weather_tool

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

_llm = ChatGroq(
    model="qwen/qwen3.8-27b",
    api_key=GROQ_API_KEY,
    temperature=0.1,
    max_tokens=800,
)

WEATHER_SYSTEM_PROMPT = """
You are a weather specialist assistant for travel planning.

Your ONLY job is to fetch accurate, real-time weather information using the weather_tool.
Given a city or destination name, call the weather_tool and return the result in this exact format:

**WEATHER**
- Condition: <description>
- Temperature: <temp>°C
- Humidity: <humidity>%

Do NOT make up weather data. Always use the tool. Be concise and factual.
"""

weather_agent = create_react_agent(
    model=_llm,
    tools=[weather_tool],
    prompt=WEATHER_SYSTEM_PROMPT,
)
