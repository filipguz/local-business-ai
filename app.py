import logging
import os

import stripe
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from ai import analyze_leads, generate_email
from auth import auth
from config import FREE_PLAN_QUERY, PRO_PLAN_QUERY
from db import get_user_plan, init_db, set_user_plan
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

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
_stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

csrf = CSRFProtect(app)
app.config["WTF_CSRF_TIME_LIMIT"] = 3600


def _rate_limit_key():
    user = session.get("user")
    return f"user:{user}" if user else get_remote_address()


limiter = Limiter(
    key_func=_rate_limit_key,
    app=app,
    storage_uri="memory://",
    default_limits=[],
)

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
    return "Payment successful"


@app.route("/cancel")
def cancel():
    return "Payment cancelled"


@app.route("/api/leads")
@limiter.limit("10 per minute")
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


@app.route("/api/email", methods=["POST"])
@limiter.limit("5 per minute")
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
        user_id = session_obj.get("metadata", {}).get("user_id")
        if not user_id:
            logger.warning("Stripe webhook: no user_id in metadata")
            return "missing user_id", 400
        set_user_plan(user_id, "pro")
        logger.info("Upgraded %s to pro", user_id)

    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
