"""Payment providers. One is shipped (Stripe); add more here and wire them in
`get_provider`. Each provider turns an amount into a remote payment intent.
"""
import os

import httpx


class StripeProvider:
    """Minimal Stripe provider using the REST API directly (no SDK dependency)."""

    name = "stripe"

    @staticmethod
    def configured() -> bool:
        return bool(os.environ.get("STRIPE_SECRET_KEY"))

    @staticmethod
    async def create_intent(amount: int, currency: str) -> dict:
        key = os.environ.get("STRIPE_SECRET_KEY")
        if not key:
            raise RuntimeError("STRIPE_SECRET_KEY is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.stripe.com/v1/payment_intents",
                data={"amount": amount, "currency": currency},
                auth=(key, ""),
            )
            resp.raise_for_status()
            data = resp.json()
            return {"reference": data["id"], "client_secret": data.get("client_secret")}


def get_provider(name: str = "stripe"):
    """Return the configured provider. Extend this for more providers."""
    if name == "stripe":
        return StripeProvider
    raise ValueError(f"Unknown payment provider: {name}")
