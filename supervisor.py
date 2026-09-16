"""
Supervisor Agent — Orchestrates all specialist sub-agents for the Travel Planner.

Architecture:
    User Query
        ↓
    Supervisor Agent (LangGraph StateGraph)
        ├── calls weather_agent   → weather data
        ├── calls places_agent    → tourist attractions
        ├── calls route_agent     → driving routes
        ├── calls railway_agent   → train schedules
        └── calls image_agent     → images (post-processing)
        ↓
    Final synthesized travel plan

The supervisor wraps each specialist agent as a @tool so the orchestrator
LLM can decide which sub-agents to invoke and in what order.
"""

import os
import re
import logging

from dotenv import load_dotenv
from typing import TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# Import API tools directly (bypasses sub-agent LLM for speed)
from tools.weather import weather_tool
from tools.places import places_tool
from tools.route import route_tool
from tools.railway import railway_tool
from agents.image_agent import image_agent

load_dotenv()

logger = logging.getLogger("supervisor")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set.")


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Supervisor Tools — call APIs directly (no sub-agent LLM overhead)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> str:
    """
    Get current weather for a city. Use whenever you need weather/forecast data.
    """
    logger.info(f"[Supervisor] → Weather Tool | city={city}")
    try:
        return weather_tool.invoke({"city": city})
    except Exception as e:
        logger.error(f"Weather tool failed: {e}")
        return f"[Weather unavailable: {e}]"


@tool
def get_places(city: str) -> str:
    """
    Get top tourist attractions in a city.
    """
    logger.info(f"[Supervisor] → Places Tool | city={city}")
    try:
        return places_tool.invoke({"city": city})
    except Exception as e:
        logger.error(f"Places tool failed: {e}")
        return f"[Places unavailable: {e}]"


@tool
def get_route(source: str, destination: str) -> str:
    """
    Calculate driving distance and route between two cities.
    """
    logger.info(f"[Supervisor] → Route Tool | {source} → {destination}")
    try:
        return route_tool.invoke({"start": source, "end": destination})
    except Exception as e:
        logger.error(f"Route tool failed: {e}")
        return f"[Route unavailable: {e}]"


@tool
def get_trains(source: str, destination: str) -> str:
    """
    Find trains between two Indian cities. Use to get train schedules.
    """
    logger.info(f"[Supervisor] → Railway Tool | {source} → {destination}")
    try:
        return railway_tool.invoke({"source": source, "destination": destination})
    except Exception as e:
        logger.error(f"Railway tool failed: {e}")
        return f"[Train info unavailable: {e}]"


# ─────────────────────────────────────────────────────────────────────────────
# Supervisor LLM + System Prompt
# ─────────────────────────────────────────────────────────────────────────────

_supervisor_llm = ChatGroq(
    model="qwen/qwen3.8-27b",
    api_key=GROQ_API_KEY,
    temperature=0.2,
    max_tokens=900,
)

SUPERVISOR_SYSTEM_PROMPT = """
You are a professional travel planner that coordinates a team of specialist agents.

You have access to these specialist agents (as tools):
- get_weather(city)       → Weather Agent (OpenWeather API)
- get_places(city)        → Places Agent  (Geoapify API)
- get_route(source, destination) → Route Agent (OpenRouteService API)
- get_trains(source, destination) → Railway Agent (RapidAPI IRCTC)

For every travel query, you MUST:
1. Call get_places() for the destination
2. Call get_weather() for the destination
3. Call get_trains() if a source city is mentioned
4. Call get_route() if the user asks about driving or distance

After collecting all data from the specialist agents, synthesize a complete travel plan
using EXACTLY this structure and section order:

**DESTINATION OVERVIEW**
(2-4 sentences about the destination)

**TOP PLACES TO VISIT**
List of at least 15 tourist attractions. Each attraction MUST:
- start on its own new line
- start with the exact marker "📍 " (emoji + space) followed by the place name and colon
- NOT wrap the place name in markdown bold, asterisks, or any other formatting
- be followed by a one-line description on the next line

Example:
📍 Calangute Beach:
Beautiful beach known for its vibrant nightlife and water sports.

📍 Fort Aguada:
Historic 17th-century Portuguese fort with panoramic sea views.

**WEATHER**
Use the data from the Weather Agent:
- Condition: <description>
- Temperature: <temp>°C
- Humidity: <humidity>%

**ITINERARY**
Day-by-day travel plan (one day per row, clearly separated).

**TRAVEL TIPS**
5-8 practical tips for visiting the destination.

**TRAIN INFORMATION**
Use ONLY the data from the Railway Agent. Show each train on its own row:
🚆 <Train Name> | Train No: <Number> | Departure: <Time>

IMPORTANT RULES:
- Show all section titles in BOLD and CAPITAL LETTERS
- Never fabricate train numbers, names, or times
- Do not put bold formatting around the 📍 attraction lines
- Only respond to travel-related queries
- Do not add any images yourself; only text
"""

# ─────────────────────────────────────────────────────────────────────────────
# Build Supervisor Agent using LangGraph StateGraph
# ─────────────────────────────────────────────────────────────────────────────

# The supervisor is itself a ReAct agent whose "tools" are the specialist agents
_supervisor_react = create_react_agent(
    model=_supervisor_llm,
    tools=[get_weather, get_places, get_route, get_trains],
    prompt=SUPERVISOR_SYSTEM_PROMPT,
)


# ─────────────────────────────────────────────────────────────────────────────
# State definition for the multi-agent graph
# ─────────────────────────────────────────────────────────────────────────────

class TravelState(TypedDict):
    query: str
    travel_plan: str
    images: list[dict]
    places: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Graph Nodes
# ─────────────────────────────────────────────────────────────────────────────

def supervisor_node(state: TravelState) -> TravelState:
    """Run the supervisor ReAct agent to produce the full travel plan."""
    logger.info("[Graph] Running Supervisor Node")
    result = _supervisor_react.invoke({
        "messages": [HumanMessage(content=state["query"])]
    })
    plan = result["messages"][-1].content
    # Extract place names for image fetching
    places = _extract_places(plan)
    logger.info(f"[Graph] Supervisor done. Found {len(places)} places.")
    return {**state, "travel_plan": plan, "places": places}


def image_node(state: TravelState) -> TravelState:
    """Run the Image Agent to fetch images for all extracted places."""
    logger.info(f"[Graph] Running Image Node for {len(state['places'])} places")
    images = image_agent(state["places"])
    return {**state, "images": images}


# ─────────────────────────────────────────────────────────────────────────────
# Helper: extract place names from the travel plan text
# ─────────────────────────────────────────────────────────────────────────────

def _extract_places(travel_plan: str) -> list[str]:
    """
    Pull place names out of lines like '📍 Calangute Beach:' or
    '📍 **Calangute Beach**:' — strips markdown and trailing colons.
    """
    matches = re.findall(r"📍\s*([^\n:]+)", travel_plan)
    places = []
    for raw in matches:
        place = raw.strip()
        place = place.replace("**", "").replace("*", "")
        place = place.rstrip(":").strip()
        place = re.sub(r"\s+", " ", place)
        if place and place not in places:
            if "TOP PLACES" not in place.upper():
                places.append(place)
    return places


# ─────────────────────────────────────────────────────────────────────────────
# Assemble the LangGraph StateGraph
# ─────────────────────────────────────────────────────────────────────────────

_graph_builder = StateGraph(TravelState)

_graph_builder.add_node("supervisor", supervisor_node)
_graph_builder.add_node("image_fetcher", image_node)

_graph_builder.set_entry_point("supervisor")
_graph_builder.add_edge("supervisor", "image_fetcher")
_graph_builder.add_edge("image_fetcher", END)

travel_graph = _graph_builder.compile()


# ─────────────────────────────────────────────────────────────────────────────
# Public-facing agent interface (same shape as the old single agent)
# ─────────────────────────────────────────────────────────────────────────────

class SupervisorAgent:
    """
    Drop-in replacement for the old single ReAct agent.
    Exposes the same .invoke() interface so api.py needs minimal changes.
    """

    def invoke(self, input_dict: dict) -> dict:
        """
        Args:
            input_dict: {"messages": [{"role": "user", "content": query}]}

        Returns:
            {"messages": [<AIMessage with travel plan>], "images": [...]}
        """
        # Extract the user query from the messages list
        messages = input_dict.get("messages", [])
        if not messages:
            raise ValueError("No messages provided to SupervisorAgent.invoke()")

        first = messages[0]
        query = first["content"] if isinstance(first, dict) else first.content

        # Run the full multi-agent graph
        result = travel_graph.invoke({
            "query": query,
            "travel_plan": "",
            "images": [],
            "places": [],
        })

        # Return in the shape api.py expects
        return {
            "messages": [AIMessage(content=result["travel_plan"])],
            "images": result["images"],
        }


# The single export used by agent.py and api.py
supervisor_agent = SupervisorAgent()
