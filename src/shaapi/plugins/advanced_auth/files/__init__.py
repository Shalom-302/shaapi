"""Advanced auth plugin — TOTP-based multi-factor authentication.

Added via `shaapi add advanced_auth`. Auto-discovered by backend/app/api.py.
Layers MFA on top of the built-in User + JWT; it does not replace them.
"""
from backend.plugins.advanced_auth.router import router

__all__ = ["router"]
