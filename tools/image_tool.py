import requests

# Wikimedia APIs explicitly require a descriptive User-Agent header
HEADERS = {
    "User-Agent": "TravelPlannerBot/1.0 (contact: travelagent@example.com)"
}


def get_cover_image(place_name):
    try:
        # 1. Clean up any accidental markdown formatting passed by the LLM
        clean_name = place_name.replace("**", "").replace("*", "").strip()
        
        # 2. Wikipedia summary API is case-sensitive (needs Title Case)
        clean_name = clean_name.title().replace(" ", "_")

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name}"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if "originalimage" in data:
                return data["originalimage"]["source"]

            if "thumbnail" in data:
                return data["thumbnail"]["source"]

    except Exception:
        pass

    return None


def get_gallery_images(place_name, limit=9):
    try:
        # Clean up accidental markdown formatting
        clean_name = place_name.replace("**", "").replace("*", "").strip()

        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": clean_name,
            "gsrnamespace": 6,  # Namespace 6 is strictly for File/Media pages
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json"
        }

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=10
        )

        data = response.json()
        images = []

        if "query" in data:
            for page in data["query"]["pages"].values():
                if "imageinfo" in page:
                    images.append(
                        page["imageinfo"][0]["url"]
                    )

                if len(images) >= limit:
                    break

        return images

    except Exception:
        return []