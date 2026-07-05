import csv
import io
import logging
import os
from datetime import timedelta

import stripe
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, redirect, render_template, request, session
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from ai import analyze_leads, generate_email
from auth import auth
from config import FREE_PLAN_QUERY, PRO_PLAN_QUERY
from db import (
    delete_saved_lead,
    get_saved_leads,
    get_user_plan,
    init_db,
    save_lead,
    set_user_plan,
    update_saved_lead,
)
from extensions import limiter
from maps import search_places
from payments import create_checkout_session

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")
app.secret_key = secret_key
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
app.config["WTF_CSRF_TIME_LIMIT"] = 3600

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
_stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

csrf = CSRFProtect(app)
limiter.init_app(app)


def _rate_limit_key():
    user = session.get("user")
    return f"user:{user}" if user else get_remote_address()


app.register_blueprint(auth)
init_db()


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/app")
def dashboard():
    if not session.get("user"):
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/checkout")
def checkout():
    if not session.get("user"):
        return redirect("/login")
    url = create_checkout_session(session["user"])
    return redirect(url)


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


@app.route("/api/leads")
@limiter.limit("10 per minute", key_func=_rate_limit_key)
def get_leads():
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    plan = get_user_plan(user)

    custom_query = request.args.get("q", "").strip()
    if custom_query:
        query = custom_query
    else:
        query = PRO_PLAN_QUERY if plan == "pro" else FREE_PLAN_QUERY

    places = search_places(query)
    leads = analyze_leads(places)

    if plan == "free":
        leads = leads[:5]
        message = "Free plan – viser 5 leads. Oppgrader for alle."
    else:
        message = "Pro plan – full tilgang"

    return jsonify({"user": user, "plan": plan, "message": message, "data": leads})


@app.route("/api/leads/save", methods=["POST"])
@limiter.limit("30 per minute", key_func=_rate_limit_key)
def save_lead_route():
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    lead = request.get_json(silent=True)
    if not lead or not lead.get("name"):
        return jsonify({"error": "Mangler lead-data"}), 400

    lead_id = save_lead(user, lead)
    return jsonify({"id": lead_id}), 201


@app.route("/api/leads/saved")
def get_saved_leads_route():
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    leads = get_saved_leads(user)
    return jsonify({"data": leads})


@app.route("/api/leads/saved/<int:lead_id>", methods=["DELETE"])
def delete_saved_lead_route(lead_id):
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    deleted = delete_saved_lead(lead_id, user)
    if not deleted:
        return jsonify({"error": "Ikke funnet"}), 404
    return jsonify({"ok": True})


@app.route("/api/leads/saved/<int:lead_id>", methods=["PATCH"])
def update_saved_lead_route(lead_id):
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    body = request.get_json(silent=True) or {}
    status = body.get("status")
    notes = body.get("notes")

    updated = update_saved_lead(lead_id, user, status, notes)
    if not updated:
        return jsonify({"error": "Ugyldig eller ikke funnet"}), 400
    return jsonify({"ok": True})


@app.route("/api/leads/saved/export")
def export_saved_leads():
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    leads = get_saved_leads(user)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["name", "industry", "website_quality", "score", "reason", "address", "status", "notes", "saved_at"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(leads)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@app.route("/api/email", methods=["POST"])
@limiter.limit("5 per minute", key_func=_rate_limit_key)
def get_lead_email():
    user = session.get("user")
    if not user:
        return jsonify({"error": "not logged in"}), 401

    plan = get_user_plan(user)
    if plan != "pro":
        return jsonify({"error": "Pro-plan kreves for å generere e-post"}), 403

    lead = request.get_json(silent=True)
    if not lead or not lead.get("name"):
        return jsonify({"error": "Mangler lead-data"}), 400

    email_text = generate_email(lead)
    return jsonify({"email": email_text})


@app.route("/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    if not _stripe_webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured")
        return "Webhook not configured", 500

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        return "Invalid signature", 400
    except Exception as e:
        logger.exception("Webhook error")
        return f"Webhook error: {e}", 400

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        username = session_obj.get("metadata", {}).get("username")
        if not username:
            logger.warning("Stripe webhook: no username in metadata")
            return "missing username", 400
        updated = set_user_plan(username, "pro")
        if not updated:
            logger.error("Stripe webhook: user '%s' not found in DB — plan not upgraded", username)
            return "user not found", 404
        logger.info("Upgraded %s to pro", username)

    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
