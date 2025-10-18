import stripe

stripe.api_key = "your_stripe_secret_key"

def create_payment_intent(amount_cents, currency="usd"):
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        payment_method_types=["card"],
    )
