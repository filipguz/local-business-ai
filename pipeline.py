import logging

from ai import analyze_leads
from maps import search_places

logger = logging.getLogger(__name__)


def run_pipeline(query: str = "bedrifter Evje Norge") -> list:
    logger.info("Søker Google Maps: %s", query)
    places = search_places(query)
    logger.info("Fant %d bedrifter", len(places))

    if not places:
        logger.warning("Ingen resultater fra Google Maps for query: %s", query)
        return []

    logger.info("Sender til AI for analyse")
    leads = analyze_leads(places)

    if not leads:
        logger.warning("AI returnerte ingen leads")

    return leads


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    output = run_pipeline("frisør Evje Norge")
    print(json.dumps(output, indent=2, ensure_ascii=False))
