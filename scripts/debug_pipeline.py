import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from ai import analyze_leads
from maps import search_places


def debug():
    print("\nHENTER FRA GOOGLE MAPS...\n")
    places = search_places("frisør Evje Norge")
    print("RAW DATA:")
    print(json.dumps(places, indent=2, ensure_ascii=False))

    print("\nSENDER TIL AI...\n")
    result = analyze_leads(places)

    print("\nRESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    debug()
