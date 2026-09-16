"""
Image Agent — Specialist agent for fetching travel images.
Uses Wikipedia & Wikimedia Commons (no API key required).
Wraps image_tool functions as a callable node for the supervisor graph.
Uses ThreadPoolExecutor to fetch all place images in parallel for speed.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from tools.image_tool import get_cover_image, get_gallery_images
import logging

logger = logging.getLogger("image_agent")

# Max parallel image fetch threads — keep reasonable to avoid hammering Wikipedia
MAX_WORKERS = 6


def _fetch_place_images(place: str) -> dict:
    """Fetch cover + gallery images for a single place."""
    try:
        cover = get_cover_image(place)
    except Exception as e:
        logger.warning(f"Cover image failed for '{place}': {e}")
        cover = None

    try:
        gallery = get_gallery_images(place)
    except Exception as e:
        logger.warning(f"Gallery failed for '{place}': {e}")
        gallery = []

    logger.info(
        f"Image Agent | Place: {place} | cover: {bool(cover)} | gallery: {len(gallery or [])}"
    )

    return {
        "name": place,
        "cover_image": cover,
        "gallery": gallery or [],
    }


def image_agent(places: list[str]) -> list[dict]:
    """
    Fetch cover image and gallery images for each place — in parallel.

    Args:
        places: List of place/attraction names.

    Returns:
        List of dicts: [{"name": str, "cover_image": str|None, "gallery": list[str]}]
    """
    if not places:
        return []

    results_map: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_place = {
            executor.submit(_fetch_place_images, place): place
            for place in places
        }
        for future in as_completed(future_to_place):
            place = future_to_place[future]
            try:
                results_map[place] = future.result()
            except Exception as e:
                logger.error(f"Image fetch crashed for '{place}': {e}")
                results_map[place] = {
                    "name": place,
                    "cover_image": None,
                    "gallery": [],
                }

    # Return in original order
    return [results_map[p] for p in places if p in results_map]
