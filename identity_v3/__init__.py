"""Evidence-calibrated, reversible identity resolution for the SISO People Graph."""

from .engine import IdentityEngine, IdentityError
from .registry import IdentifierRule, all_rules, is_auto_resolvable, normalize_name, rule_for

__all__ = [
    "IdentityEngine",
    "IdentityError",
    "IdentifierRule",
    "all_rules",
    "is_auto_resolvable",
    "normalize_name",
    "rule_for",
]

__version__ = "0.1.0"
