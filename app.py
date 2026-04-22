from flask import Flask, request, render_template_string
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Lead Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-gray-100">

<div class="flex h-screen">

    <!-- Sidebar -->
    <div class="w-64 bg-gray-900 text-white p-6">
        <h1 class="text-xl font-bold mb-4">Lead Agent</h1>

        <form method="post" class="space-y-3">
            <button name="action" value="single"
                class="w-full bg-blue-600 p-2 rounded-xl">
                Kjør 1 søk
            </button>

            <button name="action" value="auto"
                class="w-full bg-green-600 p-2 rounded-xl">
                Auto 50 leads
            </button>
        </form>

        <p class="text-xs text-gray-400 mt-6">
            Genererer lokale leads i Evje
        </p>
    </div>

    <!-- Main -->
    <div class="flex-1 p-10">

        <div class="bg-white p-6 rounded-2xl shadow h-[85vh] overflow-auto">
            <h2 class="text-lg font-semibold mb-3">Resultater</h2>
            <pre class="text-sm whitespace-pre-wrap">{{ result }}</pre>
        </div>

    </div>

</div>

</body>
</html>
"""

def run_single():
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": """
Finn 5 små bedrifter i Evje uten god nettside.
Svar strukturert med navn og bransje.
"""
        }]
    )
    return response.content[0].text


def run_auto():
    all_results = []

    for i in range(10):  # 10 x 5 leads = ~50
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": f"""
Du er en lead-genereringsagent.

Finn 5 UNIKE små bedrifter i Evje eller nærliggende områder
som har dårlig eller ingen nettside.

Tidligere funn:
{all_results}

Svar strukturert:
- Bedriftsnavn
- Bransje
- Hvorfor de er gode leads
"""
            }]
        )

        output = response.content[0].text
        all_results.append(output)

    return "\n\n---\n\n".join(all_results)


@app.route("/", methods=["GET", "POST"])
def home():
    result = ""

    if request.method == "POST":
        action = request.form.get("action")

        if action == "auto":
            result = run_auto()
        else:
            result = run_single()

    return render_template_string(HTML, result=result)


if __name__ == "__main__":
    app.run(debug=True)