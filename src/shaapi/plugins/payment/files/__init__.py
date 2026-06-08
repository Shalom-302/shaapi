"""Payment plugin — record payment intents through a pluggable provider.

Added via `shaapi add payment`. Auto-discovered by backend/app/api.py.
Ships one provider (Stripe); add more in providers.py.
"""
from backend.plugins.payment.router import router

__all__ = ["router"]
