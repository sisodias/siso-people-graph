"""Machine-readable source policies for the living-creators/media pilot.

The registry is intentionally conservative.  It records the access and
retention boundary that the adapter is designed to respect; it is not legal
advice and it does not turn a publicly visible payload into reusable content.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

POLICY_VERSION = "living-creators-source-policy-0.1"

_REQUIRED_FIELDS = {
    "source_id",
    "official_access",
    "terms_revision",
    "rights_state_default",
    "attribution",
    "quota_or_rate_limit",
    "refresh_rule",
    "deletion_update_method",
    "retention_boundary",
    "payload_boundary",
    "recommended_state",
}

SOURCE_POLICIES: dict[str, dict[str, Any]] = {
    "podcast_rss": {
        "source_id": "podcast_rss",
        "official_access": "publisher-controlled RSS/Atom feed; Podcasting 2.0 namespace where present",
        "official_docs": [
            "https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md",
            "https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/tags/person.md",
            "https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/tags/transcript.md",
        ],
        "terms_revision": "publisher feed terms are source-specific; Podcasting 2.0 namespace 1.0 reviewed 2026-08-06",
        "rights_state_default": "public_metadata",
        "attribution": "retain feed URL, publisher URL, GUID/native IDs, retrieval time, and literal field locators",
        "quota_or_rate_limit": "publisher-specific; use conditional GET and an identified user agent",
        "refresh_rule": "honour Cache-Control, ETag, Last-Modified, Retry-After, and publisher cadence",
        "deletion_update_method": "replace records by feed URL/GUID; do not infer deletion from a truncated feed alone; use explicit removal, 404/410, or publisher confirmation",
        "retention_boundary": "metadata and evidence pointers only under publisher terms; replayable raw feed only when those terms permit",
        "payload_boundary": "never acquire enclosure audio/video or transcript bodies without a separate rights gate",
        "recommended_state": "pilot_now",
    },
    "podcast_index_api": {
        "source_id": "podcast_index_api",
        "official_access": "authenticated Podcast Index API",
        "official_docs": [
            "https://github.com/Podcastindex-org/api-docs",
            "https://github.com/Podcastindex-org/legal/blob/master/TERMS.md",
        ],
        "terms_revision": "Podcast Index Terms of Service v1.1, 2021-03-02; reviewed 2026-08-06",
        "rights_state_default": "restricted",
        "attribution": "retain Podcast Index source/native IDs and API endpoint receipt",
        "quota_or_rate_limit": "credentialed access; obey response cache/rate headers and current API documentation",
        "refresh_rule": "API material is cache-header bounded; refresh only within current API terms",
        "deletion_update_method": "purge expired/terminated API cache; use publisher RSS as the durable replay path when available",
        "retention_boundary": "no permanent copy of API responses beyond the response cache boundary unless separately authorised",
        "payload_boundary": "metadata/evidence pointers only; no audio or transcript corpus",
        "recommended_state": "discovery_only",
    },
    "youtube_data_api": {
        "source_id": "youtube_data_api",
        "official_access": "YouTube Data API v3 using an API key or OAuth where required",
        "official_docs": [
            "https://developers.google.com/youtube/terms/developer-policies",
            "https://developers.google.com/youtube/terms/api-services-terms-of-service",
            "https://developers.google.com/youtube/v3/getting-started",
        ],
        "terms_revision": "YouTube Developer Policies updated 2026-05-04; data-storage policy update effective 2026-06-01",
        "rights_state_default": "restricted",
        "attribution": "retain YouTube IDs and required YouTube attribution; do not imply endorsement",
        "quota_or_rate_limit": "project quota units and endpoint-specific costs; no quota circumvention",
        "refresh_rule": "refresh or delete stored API data within 30 days unless a current documented exception applies",
        "deletion_update_method": "re-query by stable video/channel ID; remove unavailable/deleted fields and tombstone source observation without deleting evidence history",
        "retention_boundary": "source-separated refreshable metadata only; no cross-platform scoring or identity inference",
        "payload_boundary": "no video, audio, transcript, description, tags, thumbnails, comments, or statistics in this pilot",
        "recommended_state": "research_more",
    },
    "open_library_api": {
        "source_id": "open_library_api",
        "official_access": "Open Library JSON APIs for bounded use; monthly data dumps for bulk work",
        "official_docs": [
            "https://openlibrary.org/developers/api",
            "https://openlibrary.org/developers/dumps",
            "https://openlibrary.org/help/faq/about",
        ],
        "terms_revision": "Open Library developer API, dumps, and licensing guidance reviewed 2026-08-06",
        "rights_state_default": "public_metadata",
        "attribution": "retain Open Library author/work/edition keys and source locator",
        "quota_or_rate_limit": "bounded API use: identify the client; use current published limits; prefer dumps for bulk",
        "refresh_rule": "pin API retrieval or dump snapshot and replace source-native records on the next snapshot",
        "deletion_update_method": "replace by Open Library key; retain tombstone/provenance when a record disappears or redirects",
        "retention_boundary": "bibliographic metadata only; rights for linked full text remain separate",
        "payload_boundary": "no linked book payload in this adapter",
        "recommended_state": "pilot_now",
    },
    "crossref_rest_api": {
        "source_id": "crossref_rest_api",
        "official_access": "Crossref REST API and public data files where applicable",
        "official_docs": [
            "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
            "https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-metadata-license-information/",
            "https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-and-tricks/",
        ],
        "terms_revision": "Crossref REST retrieval and metadata-licensing guidance reviewed 2026-08-06",
        "rights_state_default": "public_metadata",
        "attribution": "retain DOI, member/source metadata, endpoint, and retrieval receipt",
        "quota_or_rate_limit": "use the polite pool/mailto, cache, back off, and obey current response headers",
        "refresh_rule": "refresh by DOI/update timestamp or pinned data-file snapshot",
        "deletion_update_method": "source-replace by DOI; preserve corrections/retractions and tombstones as observations",
        "retention_boundary": "metadata facts are the default; field-level licences still govern supplied content",
        "payload_boundary": "do not persist abstracts or full text unless a separate licence permits it",
        "recommended_state": "pilot_now",
    },
    "openalex_api": {
        "source_id": "openalex_api",
        "official_access": "OpenAlex API with a key for bounded calls; quarterly snapshot for bulk",
        "official_docs": [
            "https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/rate-limits-and-authentication",
            "https://docs.openalex.org/download-all-data/openalex-snapshot",
            "https://openalex.org/pricing",
        ],
        "terms_revision": "OpenAlex API authentication/pricing and snapshot documentation reviewed 2026-08-06",
        "rights_state_default": "open_data",
        "attribution": "retain OpenAlex entity IDs, snapshot/retrieval receipt, and linked authority IDs",
        "quota_or_rate_limit": "API key and metered daily credits; use snapshots for reproducible bulk work",
        "refresh_rule": "pin quarterly snapshot or retrieval date; apply source-native updated-date replacement",
        "deletion_update_method": "source-replace by OpenAlex ID and snapshot; retain redirects/tombstones and provenance",
        "retention_boundary": "open metadata observations; source-linked content rights remain separate",
        "payload_boundary": "no reconstructed abstract/full-text corpus in this pilot",
        "recommended_state": "pilot_now",
    },
    "openreview_api": {
        "source_id": "openreview_api",
        "official_access": "OpenReview API v2 for public notes and profiles; respect readers/writers fields",
        "official_docs": [
            "https://docs.openreview.net/reference/api-v2",
            "https://openreview.net/legal/terms",
        ],
        "terms_revision": "OpenReview Terms of Use last updated 2024-09-24; API v2 documentation reviewed 2026-08-06",
        "rights_state_default": "open_data",
        "attribution": "retain note/profile IDs, invitation/venue context, licence, readers, and source endpoint",
        "quota_or_rate_limit": "bounded API use with current server limits and backoff",
        "refresh_rule": "refresh by note/profile ID and modification time; keep revision lineage",
        "deletion_update_method": "honour readers/content changes and withdrawals; source-replace public fields and retain a non-public tombstone receipt",
        "retention_boundary": "public metadata only; comments/config may have different licences; private fields never enter fixtures",
        "payload_boundary": "no PDF/full text unless separately licensed",
        "recommended_state": "pilot_now",
    },
    "pretalx_schedule": {
        "source_id": "pretalx_schedule",
        "official_access": "public pretalx schedule API/export for an event whose publisher exposes it",
        "official_docs": [
            "https://docs.pretalx.org/api/fundamentals/",
            "https://docs.pretalx.org/api/resources/schedules/",
        ],
        "terms_revision": "event publisher terms are source-specific; pretalx public schedule API reviewed 2026-08-06",
        "rights_state_default": "discovery_only",
        "attribution": "retain event URL, schedule version, event/talk/person GUIDs, and publisher locator",
        "quota_or_rate_limit": "event-instance specific; use public endpoints only and back off",
        "refresh_rule": "pin schedule version; replace from latest published schedule only when deliberately requested",
        "deletion_update_method": "compare schedule versions by stable event GUID; preserve cancellation/update lineage",
        "retention_boundary": "public schedule metadata under event-publisher terms; speaker bios/contact details are excluded",
        "payload_boundary": "no recordings, slides, email-derived identifiers, or private proposal data",
        "recommended_state": "pilot_now",
    },
    "public_web_schema_org": {
        "source_id": "public_web_schema_org",
        "official_access": "explicitly supplied public page with JSON-LD/schema.org metadata; no broad crawl",
        "official_docs": [
            "https://schema.org/sameAs",
            "https://github.com/schemaorg/schemaorg",
        ],
        "terms_revision": "page terms and robots policy are source-specific; schema.org sameAs reviewed 2026-08-06",
        "rights_state_default": "discovery_only",
        "attribution": "retain page URL, retrieval receipt, JSON-LD node locator, and exact sameAs/identifier field",
        "quota_or_rate_limit": "site-specific robots/rate policy; no authentication bypass",
        "refresh_rule": "re-fetch only under page terms and robots policy; content hash every supplied page",
        "deletion_update_method": "remove/tombstone observations when the explicit page or sameAs assertion is removed or returns 404/410",
        "retention_boundary": "identifier/evidence receipts by default; raw HTML only when publisher terms permit",
        "payload_boundary": "no article/newsletter body, email address, personal notes, or inferred biography corpus",
        "recommended_state": "discovery_only",
    },
}


def validate_source_policy(policy: Mapping[str, Any]) -> None:
    missing = sorted(_REQUIRED_FIELDS.difference(policy))
    if missing:
        raise ValueError(f"source policy missing required fields: {', '.join(missing)}")
    if policy["source_id"] not in SOURCE_POLICIES:
        raise ValueError(f"unknown source policy: {policy['source_id']!r}")
    if policy["rights_state_default"] not in {
        "public_metadata",
        "open_data",
        "restricted",
        "discovery_only",
        "pending",
    }:
        raise ValueError(f"invalid rights_state_default: {policy['rights_state_default']!r}")
    if policy["recommended_state"] not in {
        "pilot_now",
        "research_more",
        "discovery_only",
        "do_not_ingest",
    }:
        raise ValueError(f"invalid recommended_state: {policy['recommended_state']!r}")
    docs = policy.get("official_docs")
    if not isinstance(docs, list) or not docs or not all(str(url).startswith("https://") for url in docs):
        raise ValueError("official_docs must be a non-empty list of HTTPS URLs")


def policy_for(source_id: str) -> dict[str, Any]:
    try:
        policy = SOURCE_POLICIES[source_id]
    except KeyError as exc:
        raise KeyError(f"no source policy registered for {source_id!r}") from exc
    validate_source_policy(policy)
    return deepcopy(policy)


def policy_registry() -> dict[str, Any]:
    for policy in SOURCE_POLICIES.values():
        validate_source_policy(policy)
    return {
        "policy_version": POLICY_VERSION,
        "sources": [deepcopy(SOURCE_POLICIES[key]) for key in sorted(SOURCE_POLICIES)],
    }
