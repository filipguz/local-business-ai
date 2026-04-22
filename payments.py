import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(user_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": os.getenv("STRIPE_PRICE_ID"),
            "quantity": 1,
        }],
        mode="subscription",
        success_url=os.getenv("DOMAIN") + "/success",
        cancel_url=os.getenv("DOMAIN") + "/cancel",
        metadata={"user_id": user_id}
    )

    return session.url