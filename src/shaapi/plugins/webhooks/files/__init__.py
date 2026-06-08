"""Webhooks plugin — register subscriptions and emit signed events.

Added via `shaapi add webhooks`. Its router is auto-discovered by
backend/app/api.py; nothing loads unless this plugin is present.
"""
from backend.plugins.webhooks.router import router

__all__ = ["router"]
