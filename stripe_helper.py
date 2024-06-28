import stripe
import os
# from dotenv import load_dotenv
import streamlit as st


# Load environment variables
openai_key = st.secrets["default"]["OPENAI_API_KEY"]
wcd_api_key = st.secrets["default"]["WCD_API_KEY"]
wcd_url = st.secrets["default"]["WCD_URL"]
stripe_secret_key = st.secrets["default"]["STRIPE_SECRET_KEY"]
success_url = st.secrets["default"]["SUCCESS_URL"]
cancel_url = st.secrets["default"]["CANCEL_URL"]

# Set Stripe API key
stripe.api_key = stripe_secret_key

def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'PDF Upload',
                    },
                    'unit_amount': 99,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url + "?session_id={CHECKOUT_SESSION_ID}",
        )
        return session
    except Exception as e:
        return str(e)

print("Ran stripe_helper.py")