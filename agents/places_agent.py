"""
Places Agent — Specialist agent powered by Geoapify API.
Responsible ONLY for fetching tourist attractions and place data.
"""

import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from tools.places import places_tool

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

PLACES_SYSTEM_PROMPT = """
You are a tourist attractions specialist for travel planning.

Your ONLY job is to fetch a list of top tourist places/attractions using the places_tool.
Given a city or destination, call places_tool and return the results in this exact format:

**TOP PLACES TO VISIT**
For each place, write:
📍 <Place Name>:
<One-line description of the place>

Rules:
- Do NOT put bold or asterisks around the place name after 📍
- Each place on its own line starting with 📍
- List at least 10-15 places if available
- Do NOT invent or add places not returned by the tool
"""

places_agent = create_react_agent(
    model=_llm,
    tools=[places_tool],
    prompt=PLACES_SYSTEM_PROMPT,
)
