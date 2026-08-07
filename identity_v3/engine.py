"""Reversible identity candidates, decisions, and canonical clusters."""
from __future__ import annotations

from ._base import (BaseMixin, IdentityError, METHOD_VERSION, UnionFind, stable_id, stable_json, utc_now)
from ._candidates import CandidateMixin
from ._clusters import ClusterMixin

class IdentityEngine(ClusterMixin, CandidateMixin, BaseMixin):
    """Identity engine operating additively inside a SQLite database."""

__all__ = [
    "IdentityEngine", "IdentityError", "METHOD_VERSION", "UnionFind",
    "stable_id", "stable_json", "utc_now",
]
