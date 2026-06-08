"""Advanced audit plugin — record and query an application audit trail.

Added via `shaapi add advanced_audit`. Auto-discovered by backend/app/api.py.
"""
from backend.plugins.advanced_audit.router import router

__all__ = ["router"]
