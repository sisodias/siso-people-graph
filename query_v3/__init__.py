"""Read-only, evidence-first query surface over the People Graph.

Public entry point. Every other surface -- CLI (`loaders/ask.py`), HTTP API
(`api/`), MCP (`mcp/`), viewer (`viewer/`) -- imports QueryEngine from here and
adds no SQL of its own.
"""
from .engine import QueryEngine
from .response import SCHEMA_VERSION

__all__ = ["QueryEngine", "SCHEMA_VERSION", "__version__"]
__version__ = "0.1.0"
