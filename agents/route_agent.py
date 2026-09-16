"""
Route Agent — Specialist agent powered by OpenRouteService (ORS) API.
Responsible ONLY for calculating distances and driving routes between cities.
"""

import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from tools.route import route_tool

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

ROUTE_SYSTEM_PROMPT = """
You are a route and distance specialist for travel planning.

Your ONLY job is to calculate driving routes and distances between two cities using route_tool.
Given a source city and a destination city, call route_tool and return the result in this format:

**ROUTE INFORMATION**
- From: <source city>
- To: <destination city>
- Distance: <distance in km>
- Estimated Drive Time: <time>

Be concise. Do NOT make up distances. Always use the route_tool.
"""

route_agent = create_react_agent(
    model=_llm,
    tools=[route_tool],
    prompt=ROUTE_SYSTEM_PROMPT,
)
