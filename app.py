from flask import Flask, render_template, jsonify
from maps import search_places
from ai import analyze_leads

app = Flask(__name__)


# 🌐 LANDING PAGE
@app.route("/")
def landing():
    return render_template("landing.html")


# 📊 DASHBOARD (APP)
@app.route("/app")
def dashboard():
    return render_template("dashboard.html")


# 🔥 API
@app.route("/api/leads")
def get_leads():
    places = search_places("frisør rørlegger Evje Norge")
    leads = analyze_leads(places)

    return jsonify(leads)


# 🚀 RENDER COMPAT
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)