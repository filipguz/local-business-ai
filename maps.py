import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def search_places(query: str) -> list:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": _API_KEY,
        "region": "no",
        "language": "no",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    logger.debug("Google Maps returned %d results for query: %s", len(data.get("results", [])), query)

    return [
        {
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating", 0),
            "types": place.get("types", []),
        }
        for place in data.get("results", [])
    ]
