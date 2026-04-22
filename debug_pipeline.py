import json
from maps import search_places
from ai import analyze_leads


def debug():
    print("\n🔎 HENTER FRA GOOGLE MAPS...\n")

    places = search_places("frisør Evje Norge")

    print("RAW DATA:")
    print(json.dumps(places, indent=2, ensure_ascii=False))

    print("\n🧠 SENDER TIL AI...\n")

    result = analyze_leads(places)

    print("\n🤖 RESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    debug()