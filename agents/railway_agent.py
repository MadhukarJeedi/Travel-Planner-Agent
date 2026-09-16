"""
Railway Agent — Specialist agent powered by RapidAPI (IRCTC).
Responsible ONLY for fetching Indian railway train information between cities.
"""

import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from tools.railway import railway_tool

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

_llm = ChatGroq(
    model="qwen/qwen3.8-27b",
    api_key=GROQ_API_KEY,
    temperature=0.0,   # Zero temperature: strictly report what the API returns
    max_tokens=800,
)

RAILWAY_SYSTEM_PROMPT = """
You are an Indian railway information specialist for travel planning.

Your ONLY job is to find trains between two cities using the railway_tool.
Given a source city and a destination city, call railway_tool and return results in this format:

**TRAIN INFORMATION**
🚆 <Train Name> | Train No: <Number> | Departure: <Time>

Rules:
- NEVER fabricate train names, numbers, or times
- Only report exactly what railway_tool returns
- List each train on its own separate row
- If no trains found, clearly state that
"""

railway_agent = create_react_agent(
    model=_llm,
    tools=[railway_tool],
    prompt=RAILWAY_SYSTEM_PROMPT,
)
