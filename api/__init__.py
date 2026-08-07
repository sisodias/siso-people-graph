"""Read-only API surface over QueryEngine.

Exports `build_server` so tests can drive the HTTP surface without spawning a
process. See api.server for the rationale (zero SQL, no write endpoints, loopback
bind by default).
"""
from .server import build_server

__all__ = ["build_server"]
