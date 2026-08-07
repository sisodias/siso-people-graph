"""Read-only HTML viewer over QueryEngine responses.

Exports `render(result)` -- a self-contained HTML string with no external
assets. Every value that came from the database is html.escape()'d before
serialisation.
"""
from .explorer import render

__all__ = ["render"]
