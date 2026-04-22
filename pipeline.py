from maps import search_places
from ai import analyze_leads

def run_pipeline(query="bedrifter Evje Norge"):
    print("🔎 Henter data fra Google Maps...")

    places = search_places(query)

    print(f"📍 Fant {len(places)} bedrifter")

    print("🧠 Sender til AI for analyse...")

    result = analyze_leads(places)

    return result


if __name__ == "__main__":
    output = run_pipeline("frisør Evje Norge")

    print("\n\n===== RESULT =====\n")
    print(output)