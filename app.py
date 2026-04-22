from flask import Flask, render_template, jsonify
from maps import search_places
from ai import analyze_leads

app = Flask(__name__)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/leads")
def get_leads():
    places = search_places("frisør rørlegger Evje Norge")
    leads = analyze_leads(places)
    return jsonify(leads)


if __name__ == "__main__":
    app.run(debug=True)