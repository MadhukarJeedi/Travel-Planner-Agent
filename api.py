
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent import agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("travel_api")

app = FastAPI(
    title="AI Travel Planner API",
    version="2.0.0"
)


class TravelRequest(BaseModel):
    query: str


@app.post("/travel")
def travel_planner(request: TravelRequest):

    if not request.query or not request.query.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Query cannot be empty."}
        )

    try:
        # SupervisorAgent.invoke() returns {"messages": [...], "images": [...]}
        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.query
                    }
                ]
            }
        )
    except Exception as e:
        logger.exception("Agent invocation failed")
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": f"Travel agent failed: {e}"}
        )

    try:
        travel_plan = response["messages"][-1].content
    except (KeyError, IndexError, AttributeError) as e:
        logger.exception("Unexpected agent response shape")
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": f"Unexpected agent response: {e}"}
        )

    # Images are now provided directly by the Image Agent inside the supervisor graph.
    # No need to re-fetch; just pass them through.
    images = response.get("images", [])

    logger.info(f"Travel plan generated | images fetched: {len(images)}")

    return {
        "status": "success",
        "query": request.query,
        "response": travel_plan,
        "images": images
    }
