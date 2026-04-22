import json
import logging
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

from config import AI_MODEL

load_dotenv()

logger = logging.getLogger(__name__)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _clean_json(text: str) -> str:
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def analyze_leads(places: list) -> list:
    places_text = json.dumps(places[:15], indent=2, ensure_ascii=False)

    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""
Du er en lead-analyse AI for webdesign.

VIKTIG:
Returner KUN gyldig JSON array.
Ingen markdown. Ingen forklaring. Ingen tekst.

FORMAT:
[
  {{
    "name": "string",
    "industry": "string",
    "website_quality": "god/dårlig/ingen/ukjent",
    "score": 1,
    "reason": "kort forklaring"
  }}
]

DATA:
{places_text}
"""
        }]
    )

    raw = response.content[0].text

    try:
        return json.loads(_clean_json(raw))
    except Exception:
        logger.exception("JSON parsing failed. Raw response: %s", raw)
        return []


def generate_email(lead: dict) -> str:
    name = lead.get("name", "")
    industry = lead.get("industry", "")
    website_quality = lead.get("website_quality", "ukjent")
    reason = lead.get("reason", "")

    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""
Du er en selger for et webdesignbyrå som tilbyr moderne nettsider til lokale bedrifter.

Skriv en kort, vennlig og konkret salgs-e-post til denne bedriften.

BEDRIFT:
Navn: {name}
Bransje: {industry}
Nettside-kvalitet: {website_quality}
Analyse: {reason}

KRAV:
- Maks 120 ord
- Norsk bokmål
- Naturlig og personlig tone – ikke korporativt
- Nevn ett konkret problem de har basert på analysen
- Avslutt med ett konkret tilbud: gratis 30-minutters gjennomgang
- Ingen klisjeer som "ta bedriften til neste nivå"

Returner KUN e-postteksten. Ingen emnelinje, ingen annen tekst.
"""
        }]
    )

    return response.content[0].text.strip()
