import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def search_places(query):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": query,
        "key": API_KEY,
        "region": "no",
        "language": "no"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # DEBUG (VIKTIG)
    print("GOOGLE RAW RESPONSE:", data)

    results = []

    for place in data.get("results", []):
        results.append({
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating", 0),
            "types": place.get("types", [])
        })

    return results