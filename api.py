
import logging
import re
 
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
 
from agent import agent
from tools.image_tool import (
    get_cover_image,
    get_gallery_images
)
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("travel_api")
 
app = FastAPI(
    title="AI Travel Planner API",
    version="1.0.0"
)
 
 
class TravelRequest(BaseModel):
    query: str
 
 
def extract_places(travel_plan: str) -> list[str]:
    """
    Pull place names out of lines like '📍 Calangute Beach:' or
    '📍 **Calangute Beach**:' - strips markdown bold/asterisks and
    trailing colons so parsing survives minor formatting drift.
    """
    matches = re.findall(r"📍\s*([^\n:]+)", travel_plan)

    places = []
    for raw in matches:
        place = raw.strip()
        place = place.replace("**", "").replace("*", "") # Remove markdown bold tags
        place = place.rstrip(":").strip()               # Remove trailing colons
        place = re.sub(r"\s+", " ", place)              # Clean up double spaces

        if place and place not in places:
            if "TOP PLACES" not in place.upper():       # Exclude header accidents
                places.append(place)

    return places
 
@app.post("/travel")
def travel_planner(request: TravelRequest):
 
    if not request.query or not request.query.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Query cannot be empty."}
        )
 
    try:
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
 
    places = extract_places(travel_plan)
 
    images = []
 
    for place in places:
        try:
            cover = get_cover_image(place)
        except Exception as e:
            logger.warning(f"Cover image lookup failed for '{place}': {e}")
            cover = None
 
        try:
            gallery = get_gallery_images(place)
        except Exception as e:
            logger.warning(f"Gallery image lookup failed for '{place}': {e}")
            gallery = []
 
        logger.info(f"Place: {place} | cover: {bool(cover)} | gallery: {len(gallery or [])}")
 
        images.append(
            {
                "name": place,
                "cover_image": cover,
                "gallery": gallery
            }
        )
 
    return {
        "status": "success",
        "query": request.query,
        "response": travel_plan,
        "images": images
    }
 
