import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from anthropic import Anthropic
from dotenv import load_dotenv

from config import AI_MODEL

load_dotenv()
logging.basicConfig(level=logging.INFO)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

GOAL = "Finn 10 små bedrifter i Evje uten god nettside"
memory: list[str] = []

for i in range(3):
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"""
Du er en research-agent som finner lokale bedrifter.

MÅL:
{GOAL}

TIDLIGERE FUNN:
{memory}

VIKTIG:
- Ikke gjenta bedrifter som allerede finnes i memory
- Finn nye unike bedrifter
- Fokuser på små lokale bedrifter i Evje

Svar strukturert:

Navn: ...
Bransje: ...
Nettside: dårlig / ingen / ukjent
Begrunnelse: ...
"""
        }]
    )

    output = response.content[0].text
    print(output)
    memory.append(output.split("\n")[0])
