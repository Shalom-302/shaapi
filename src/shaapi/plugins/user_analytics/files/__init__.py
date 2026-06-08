"""User analytics plugin — record events and query aggregated stats.

Added via `shaapi add user_analytics`. Auto-discovered by backend/app/api.py.
"""
from backend.plugins.user_analytics.router import router

__all__ = ["router"]
