from flask import Flask, render_template, jsonify, request, redirect, session
from maps import search_places
from ai import analyze_leads
from auth import auth
from payments import create_checkout_session
import os
import stripe
import json

# --------------------
# APP SETUP
# --------------------
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this")

# --------------------
# STRIPE SETUP
# --------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


# --------------------
# AUTH BLUEPRINT
# --------------------
app.register_blueprint(auth)


# --------------------
# HELPERS
# --------------------
def load_users():
    try:
        with open("users.json") as f:
            return json.load(f)
    except:
        return {}

def get_user_plan(username):
    users = load_users()
    return users.get(username, {}).get("plan", "free")


# --------------------
# PAGES
# --------------------

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


# --------------------
# STRIPE CHECKOUT
# --------------------
@app.route("/checkout")
def checkout():
    if not session.get("user"):
        return redirect("/login")

    url = create_checkout_session(session["user"])
    return redirect(url)


@app.route("/success")
def success():
    return "Payment successful 🚀"


@app.route("/cancel")
def cancel():
    return "Payment cancelled"


# --------------------
# LEADS API (WITH LIMITS)
# --------------------
@app.route("/api/leads")
def get_leads():
    user = session.get("user")

    if not user:
        return jsonify({"error": "not logged in"}), 401

    plan = get_user_plan(user)

    # 🔥 FREE vs PRO LOGIC
    if plan == "free":
        query = "frisør rørlegger Evje Norge"
        limit_message = "Free plan (limited results)"
    else:
        query = "frisør rørlegger camping hotell håndverk Evje Norge"
        limit_message = "Pro plan (full access)"

    places = search_places(query)
    leads = analyze_leads(places)

    return jsonify({
        "user": user,
        "plan": plan,
        "message": limit_message,
        "data": leads
    })


@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    import stripe
    import json

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except Exception as e:
        return f"Webhook error: {str(e)}", 400

    # 🎯 CHECKOUT COMPLETED
    if event["type"] == "checkout.session.completed":

        session_obj = event["data"]["object"]

        # safety check
        user_id = session_obj.get("metadata", {}).get("user_id")

        if not user_id:
            print("No user_id in metadata")
            return "missing user_id", 400

        users = load_users()

        if user_id in users:
            users[user_id]["plan"] = "pro"

            with open("users.json", "w") as f:
                json.dump(users, f, indent=2)

            print(f"🚀 Upgraded {user_id} to PRO")

    return "ok", 200

# --------------------
# RENDER START
# --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)