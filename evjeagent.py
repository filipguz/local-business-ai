import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

GOAL = "Finn 10 små bedrifter i Evje uten god nettside"

memory = []

for i in range(3):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": f"""
Du er en research-agent.

Mål: {GOAL}

Tidligere funn:
{memory}

Finn nye resultater som ikke er listet før.
Svar strukturert:
- Bedriftsnavn
- Bransje
- Hvorfor dårlig nettside
"""
            }
        ]
    )

    output = response.content[0].text
    print(output)

    memory.append(output)