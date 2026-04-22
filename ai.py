import os
import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def clean_json(text):
    # fjerner markdown ```json og ```
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def analyze_leads(places):
    places_text = json.dumps(places, indent=2, ensure_ascii=False)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
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
        cleaned = clean_json(raw)
        return json.loads(cleaned)

    except Exception as e:
        return {
            "error": "JSON parsing feilet",
            "exception": str(e),
            "raw": raw
        }