"""MCP read-only surface over QueryEngine.

Exposes `handle` so tests can dispatch synthetic JSON-RPC requests without
spawning a subprocess or wiring up stdio.
"""
from .server import TOOLS, handle

__all__ = ["TOOLS", "handle"]
