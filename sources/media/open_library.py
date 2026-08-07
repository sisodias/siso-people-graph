"""Open Library author/work/edition metadata mapper."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from sources.creators.envelope import evidence, identifier, make_envelope, payload_sha256
from sources.media.common import SourceContext, agent, contribution, first_text, relationship
from sources.media.policies import SOURCE_POLICIES

_POLICY = SOURCE_POLICIES["open_library_api"]
TERMS_REVISION = _POLICY["terms_revision"]


def _context(payload: Mapping[str, Any], endpoint: str, retrieved_at: str) -> SourceContext:
    digest = payload_sha256(payload)
    revision = payload.get("last_modified") or payload.get("created") or {}
    observed_at = revision.get("value") if isinstance(revision, Mapping) else retrieved_at
    return SourceContext(
        source_id="open_library_api",
        snapshot_id=f"sha256:{digest}",
        observed_at=first_text(observed_at, retrieved_at),
        retrieved_at=retrieved_at,
        terms_revision=TERMS_REVISION,
        rights_state=_POLICY["rights_state_default"],
        raw_pointer=endpoint,
    )


def _key(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return str(value.get("key") or "")
    return ""


def adapt_author(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    context = _context(payload, endpoint, retrieved_at)
    author_key = _key(payload.get("key"))
    if not author_key:
        raise ValueError("Open Library author payload has no key")
    label = first_text(payload.get("name"), default=author_key)
    identifiers = [
        identifier(
            scheme="open_library_author_id",
            value=author_key,
            scope="source",
            stability="stable",
            uniqueness="unique",
            evidence=f"{endpoint} key",
        )
    ]
    remote_ids = payload.get("remote_ids") if isinstance(payload.get("remote_ids"), Mapping) else {}
    for field, scheme in (("wikidata", "wikidata"), ("viaf", "viaf"), ("isni", "isni")):
        value = remote_ids.get(field)
        if value:
            identifiers.append(
                identifier(
                    scheme=scheme,
                    value=str(value),
                    scope="global",
                    stability="stable",
                    uniqueness="unique",
                    evidence=f"{endpoint} remote_ids.{field}",
                )
            )
    links = payload.get("links") if isinstance(payload.get("links"), list) else []
    for index, link in enumerate(links):
        if not isinstance(link, Mapping) or not link.get("url"):
            continue
        identifiers.append(
            identifier(
                scheme="same_as_url",
                value=str(link["url"]),
                scope="global",
                stability="unknown",
                uniqueness="unknown",
                evidence=f"{endpoint} links[{index}].url",
            )
        )
    return make_envelope(
        source=context.block(author_key, payload),
        subject_kind="person",
        subject_native_id=author_key,
        label=label,
        attributes={
            "birth_date": payload.get("birth_date"),
            "death_date": payload.get("death_date"),
            "alternate_name_count": len(payload.get("alternate_names", []))
            if isinstance(payload.get("alternate_names"), list)
            else 0,
            "bio_persisted": False,
            "photo_persisted": False,
        },
        identifiers=identifiers,
        contributions=[],
        relationships=[],
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#author-{author_key}",
                literal=label,
                source_field="name",
            )
        ],
        raw_pointer=endpoint,
    )


def _author_contributions(
    authors: Sequence[Any], endpoint: str, record_id: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(authors):
        key = _key(raw.get("author") if isinstance(raw, Mapping) else raw)
        if not key:
            continue
        label = first_text(raw.get("name") if isinstance(raw, Mapping) else None, default=key)
        rows.append(
            contribution(
                role="author",
                agent_record=agent(
                    source_native_id=key,
                    label=label,
                    kind="unknown",
                    identifiers=[
                        identifier(
                            scheme="open_library_author_id",
                            value=key,
                            scope="source",
                            stability="stable",
                            uniqueness="unique",
                            evidence=f"{endpoint} {record_id}.authors[{index}]",
                        )
                    ],
                ),
                evidence=f"{endpoint} {record_id}.authors[{index}]",
                order=index + 1,
                identity_evidence="source_native",
            )
        )
    return rows


def adapt_work(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    context = _context(payload, endpoint, retrieved_at)
    work_key = _key(payload.get("key"))
    if not work_key:
        raise ValueError("Open Library work payload has no key")
    title = first_text(payload.get("title"), default=work_key)
    return make_envelope(
        source=context.block(work_key, payload),
        subject_kind="work",
        subject_native_id=work_key,
        label=title,
        attributes={
            "work_type": "book",
            "first_publish_date": payload.get("first_publish_date"),
            "subject_count": len(payload.get("subjects", []))
            if isinstance(payload.get("subjects"), list)
            else 0,
            "description_persisted": False,
            "full_text_persisted": False,
        },
        identifiers=[
            identifier(
                scheme="open_library_work_id",
                value=work_key,
                scope="source",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} key",
            )
        ],
        contributions=_author_contributions(payload.get("authors", []), endpoint, work_key),
        relationships=[],
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#work-{work_key}",
                literal=title,
                source_field="title",
            )
        ],
        raw_pointer=endpoint,
    )


def adapt_edition(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    context = _context(payload, endpoint, retrieved_at)
    edition_key = _key(payload.get("key"))
    if not edition_key:
        raise ValueError("Open Library edition payload has no key")
    title = first_text(payload.get("title"), default=edition_key)
    works = payload.get("works") if isinstance(payload.get("works"), list) else []
    relationships = []
    for index, work in enumerate(works):
        work_key = _key(work)
        if work_key:
            relationships.append(
                relationship(
                    predicate="edition_of",
                    object_kind="work",
                    object_native_id=work_key,
                    object_label=work_key,
                    evidence=f"{endpoint} works[{index}]",
                )
            )
    identifiers = [
        identifier(
            scheme="open_library_edition_id",
            value=edition_key,
            scope="source",
            stability="stable",
            uniqueness="unique",
            evidence=f"{endpoint} key",
        )
    ]
    for index, isbn in enumerate(payload.get("isbn_13", []) if isinstance(payload.get("isbn_13"), list) else []):
        identifiers.append(
            identifier(
                scheme="isbn13",
                value=str(isbn),
                scope="global",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} isbn_13[{index}]",
            )
        )
    return make_envelope(
        source=context.block(edition_key, payload),
        subject_kind="work",
        subject_native_id=edition_key,
        label=title,
        attributes={
            "work_type": "book_edition",
            "publish_date": payload.get("publish_date"),
            "publishers": payload.get("publishers", []),
            "full_text_persisted": False,
        },
        identifiers=identifiers,
        contributions=_author_contributions(payload.get("authors", []), endpoint, edition_key),
        relationships=relationships,
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#edition-{edition_key}",
                literal=title,
                source_field="title",
            )
        ],
        raw_pointer=endpoint,
    )
