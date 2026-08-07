"""Identifier policy and Unicode-safe comparison helpers.

The registry is deliberately explicit: only schemes marked auto-resolution
eligible may ever drive an automatic identity decision. Everything else is an
alias, attribute, metric, or unclassified source field.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import unicodedata
from urllib.parse import urlparse
from typing import Dict, Iterable, Mapping


@dataclass(frozen=True)
class IdentifierRule:
    scheme: str
    category: str  # identifier | alias | attribute | metric | unknown
    scope: str  # global | source | organisation | none
    uniqueness: str  # unique | non_unique | unknown
    mutability: str  # immutable | stable | mutable | unknown
    authority: str
    auto_resolution_eligible: bool
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


_RULES: tuple[IdentifierRule, ...] = (
    IdentifierRule("github_id", "identifier", "source", "unique", "immutable", "github", True,
                   "GitHub numeric account id; survives login changes."),
    IdentifierRule("github_node_id", "identifier", "source", "unique", "immutable", "github", True,
                   "GitHub GraphQL node id."),
    IdentifierRule("orcid", "identifier", "global", "unique", "stable", "orcid", True,
                   "ORCID researcher identifier."),
    IdentifierRule("viaf", "identifier", "global", "unique", "stable", "viaf", True,
                   "VIAF authority cluster identifier."),
    IdentifierRule("isni", "identifier", "global", "unique", "stable", "isni", True,
                   "ISNI public identity identifier."),
    IdentifierRule("wikidata", "identifier", "global", "unique", "stable", "wikidata", True,
                   "Wikidata Q identifier."),
    IdentifierRule("loc_authority", "identifier", "global", "unique", "stable", "loc", True,
                   "Library of Congress authority identifier."),
    IdentifierRule("openalex_author_id", "identifier", "source", "unique", "stable", "openalex", True,
                   "OpenAlex author identifier."),
    IdentifierRule("dblp_pid", "identifier", "source", "unique", "stable", "dblp", True,
                   "DBLP person identifier."),
    IdentifierRule("youtube_channel_id", "identifier", "source", "unique", "stable", "youtube", True,
                   "YouTube channel id; channel ownership still needs evidence."),
    IdentifierRule("software_heritage_origin", "identifier", "source", "unique", "stable", "software_heritage", False,
                   "Identifies an archived origin, not necessarily a person."),
    IdentifierRule("github_login", "alias", "source", "unique", "mutable", "github", False,
                   "Mutable GitHub username linked to a stable account id."),
    IdentifierRule("x_handle", "alias", "source", "unknown", "mutable", "x", False,
                   "Mutable account handle; never automatic identity evidence."),
    IdentifierRule("username", "alias", "source", "unknown", "mutable", "source", False,
                   "Generic mutable username."),
    IdentifierRule("real_name", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Source-observed display name, not an identifier."),
    IdentifierRule("name", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Human-readable name, never globally unique."),
    IdentifierRule("company", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Affiliation-like source field, not an identity key."),
    IdentifierRule("location", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Location text, not an identity key."),
    IdentifierRule("topic", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Topic label, not an identity key."),
    IdentifierRule("biography", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Biography text, not an identity key."),
    IdentifierRule("bio", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Biography text, not an identity key."),
    IdentifierRule("website", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Website locator; shared and transferable, so review evidence only."),
    IdentifierRule("profile_type", "attribute", "none", "non_unique", "mutable", "source", False,
                   "Source account type observation."),
    IdentifierRule("account_created_at", "attribute", "none", "non_unique", "stable", "source", False,
                   "Source account creation timestamp."),
    IdentifierRule("followers", "metric", "none", "non_unique", "mutable", "source", False,
                   "Timestamped popularity metric, never identity evidence."),
    IdentifierRule("follower_count", "metric", "none", "non_unique", "mutable", "source", False,
                   "Timestamped popularity metric, never identity evidence."),
)

_RULE_BY_SCHEME: Dict[str, IdentifierRule] = {rule.scheme: rule for rule in _RULES}
_UNKNOWN = IdentifierRule(
    "unknown", "unknown", "none", "unknown", "unknown", "unclassified", False,
    "Unregistered schemes are quarantined from automatic resolution.",
)


def all_rules() -> tuple[IdentifierRule, ...]:
    return _RULES


def rule_for(scheme: str) -> IdentifierRule:
    key = (scheme or "").strip().casefold()
    return _RULE_BY_SCHEME.get(key, IdentifierRule(
        key or "unknown", _UNKNOWN.category, _UNKNOWN.scope, _UNKNOWN.uniqueness,
        _UNKNOWN.mutability, _UNKNOWN.authority, False, _UNKNOWN.description,
    ))


def is_auto_resolvable(scheme: str) -> bool:
    rule = rule_for(scheme)
    return (
        rule.category == "identifier"
        and rule.uniqueness == "unique"
        and rule.auto_resolution_eligible
    )


# Values that are syntactically valid for their scheme but encode "absent",
# "deleted", or "unknown" rather than one account. Measured on the shipped
# graph-v2 asset: 58,509 crates.io-derived rows carry github_id=0 or -1 as a
# "no GitHub account" sentinel, which made 18 distinct humans share one
# "unique" identifier. Treating absence as an identity is the failure mode
# METHOD_CARD lists as blind spot 2 ("identifier reuse"), so it is blocked
# here, at the policy layer, rather than in any one caller.
_NUMERIC_SENTINELS = {"0", "-1", "-99", "99999999"}
_TEXT_SENTINELS = {
    "none", "null", "nil", "n/a", "na", "unknown", "undefined", "ghost",
    "deleted", "deleted-user", "anonymous", "unclaimed", "placeholder",
}


def is_sentinel_value(scheme: str, normalized_value: str) -> bool:
    """True when a normalized identifier encodes absence rather than identity."""
    text = (normalized_value or "").strip()
    if not text:
        return True
    folded = text.casefold()
    if folded in _TEXT_SENTINELS:
        return True
    key = (scheme or "").strip().casefold()
    if key in {"github_id", "github_node_id"} and text in _NUMERIC_SENTINELS:
        return True
    # A purely numeric account id of 0 or negative is never a real account.
    if key == "github_id":
        try:
            if int(text) <= 0:
                return True
        except ValueError:
            pass
    if key == "orcid" and set(text) <= {"0", "-", "X"}:
        return True
    if key == "wikidata" and folded in {"q0", "q"}:
        return True
    return False


def normalize_identifier(scheme: str, value: object) -> str:
    """Normalize source identifiers without turning names into identifiers."""
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    key = (scheme or "").strip().casefold()
    if not text:
        return ""
    if key == "github_id":
        try:
            return str(int(text))
        except ValueError:
            return text
    if key in {"github_node_id", "youtube_channel_id"}:
        # Opaque platform identifiers may be case-sensitive; never casefold
        # them merely for convenience.
        return text
    if key in {"github_login", "x_handle", "username"}:
        return text.lstrip("@").casefold()
    if key == "orcid":
        low = text.casefold().replace("https://orcid.org/", "")
        compact = re.sub(r"[^0-9xX]", "", low).upper()
        if len(compact) == 16:
            return "-".join(compact[i:i + 4] for i in range(0, 16, 4))
        return text.upper()
    if key == "wikidata":
        match = re.search(r"(?:^|/)(Q\d+)$", text, re.IGNORECASE)
        return (match.group(1) if match else text).upper()
    if key in {"viaf", "isni", "loc_authority", "openalex_author_id", "dblp_pid"}:
        return text.strip().casefold()
    if key == "website":
        parsed = urlparse(text if "://" in text else f"https://{text}")
        host = (parsed.hostname or "").casefold()
        path = parsed.path.rstrip("/")
        return f"{host}{path}" if host else text.casefold().rstrip("/")
    return text.casefold()


_NOISE_TOKENS = {
    "sir", "dame", "lord", "lady", "baron", "baroness", "earl", "duke",
    "rev", "dr", "prof", "jr", "sr", "saint", "st", "mrs", "mr", "ms",
}


def normalize_name(value: object) -> str:
    """Unicode-preserving comparison key.

    This key is never used to mint an entity id. NFKC and casefold normalize
    representation while letters and combining marks from every script survive.
    Punctuation and symbols become separators rather than being transliterated
    or dropped into accidental collisions.
    """
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"\([^)]*\)", " ", text)
    chars: list[str] = []
    for char in text:
        category = unicodedata.category(char)
        if category[0] in {"L", "N", "M"}:
            chars.append(char)
        else:
            chars.append(" ")
    tokens = [token for token in "".join(chars).split() if token not in _NOISE_TOKENS]
    return " ".join(tokens)


def name_parts(value: object) -> tuple[str, str]:
    """Return comparison-only surname and given-name components."""
    raw = unicodedata.normalize("NFKC", str(value or ""))
    if "," in raw:
        surname_raw, given_raw = raw.split(",", 1)
        return normalize_name(surname_raw), normalize_name(given_raw)
    normalized = normalize_name(raw)
    tokens = normalized.split()
    if len(tokens) >= 2:
        return tokens[-1], " ".join(tokens[:-1])
    return normalized, ""


def years_compatible(a: tuple[int | None, int | None], b: tuple[int | None, int | None], tolerance: int = 2) -> bool:
    (birth_a, death_a), (birth_b, death_b) = a, b
    if birth_a is not None and birth_b is not None and abs(birth_a - birth_b) > tolerance:
        return False
    if death_a is not None and death_b is not None and abs(death_a - death_b) > tolerance:
        return False
    return True


def registry_as_dict() -> Mapping[str, Mapping[str, object]]:
    return {rule.scheme: rule.as_dict() for rule in _RULES}
