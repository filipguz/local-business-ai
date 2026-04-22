import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

GOAL = "Finn 10 små bedrifter i Evje uten god nettside"

# 🧠 strukturert memory (ikke tekst)
memory = []

for i in range(3):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[
            {
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
            }
        ]
    )

    output = response.content[0].text
    print(output)

    # 🧠 lagre kun navn (bedre memory)
    memory.append(output.split("\n")[0])