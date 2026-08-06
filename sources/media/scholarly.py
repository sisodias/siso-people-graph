"""Crossref, OpenAlex and OpenReview metadata adapters."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from sources.creators.envelope import evidence, identifier, make_envelope, payload_sha256
from sources.media.common import SourceContext, agent, contribution, first_text, relationship
from sources.media.policies import SOURCE_POLICIES


def _context(
    *,
    source_id: str,
    payload: Mapping[str, Any],
    endpoint: str,
    retrieved_at: str,
    terms_revision: str,
    rights_state: str,
    observed_at: str | None = None,
) -> SourceContext:
    digest = payload_sha256(payload)
    return SourceContext(
        source_id=source_id,
        snapshot_id=f"sha256:{digest}",
        observed_at=observed_at or retrieved_at,
        retrieved_at=retrieved_at,
        terms_revision=terms_revision,
        rights_state=rights_state,
        raw_pointer=endpoint,
    )


def _crossref_name(author: Mapping[str, Any]) -> str:
    return " ".join(
        part.strip()
        for part in (str(author.get("given") or ""), str(author.get("family") or ""))
        if part.strip()
    ) or first_text(author.get("name"))


def adapt_crossref_work(
    *, item: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    doi = first_text(item.get("DOI"), item.get("URL"))
    if not doi:
        raise ValueError("Crossref item has no DOI/URL")
    title_values = item.get("title", [])
    title = first_text(title_values[0] if isinstance(title_values, list) and title_values else title_values, default=doi)
    context = _context(
        source_id="crossref_rest_api",
        payload=item,
        endpoint=endpoint,
        retrieved_at=retrieved_at,
        terms_revision=SOURCE_POLICIES["crossref_rest_api"]["terms_revision"],
        rights_state=SOURCE_POLICIES["crossref_rest_api"]["rights_state_default"],
        observed_at=first_text(item.get("indexed", {}).get("date-time") if isinstance(item.get("indexed"), Mapping) else None, retrieved_at),
    )
    contributors: list[dict[str, Any]] = []
    for role_field, role in (("author", "author"), ("editor", "editor"), ("translator", "translator")):
        values = item.get(role_field, [])
        if not isinstance(values, list):
            continue
        for index, raw in enumerate(values):
            if not isinstance(raw, Mapping):
                continue
            label = _crossref_name(raw)
            if not label:
                continue
            orcid = first_text(raw.get("ORCID")).replace("https://orcid.org/", "")
            native_id = f"orcid:{orcid}" if orcid else f"{doi}#{role_field}-{index}"
            ids = []
            identity_evidence = "name_only"
            if orcid:
                ids.append(
                    identifier(
                        scheme="orcid",
                        value=orcid,
                        scope="global",
                        stability="stable",
                        uniqueness="unique",
                        evidence=f"{endpoint} {role_field}[{index}].ORCID",
                    )
                )
                identity_evidence = "authority_identifier"
            contributors.append(
                contribution(
                    role=role,
                    agent_record=agent(
                        source_native_id=native_id,
                        label=label,
                        kind="unknown",
                        identifiers=ids,
                    ),
                    evidence=f"{endpoint} {role_field}[{index}]",
                    order=index + 1,
                    identity_evidence=identity_evidence,
                )
            )
    return make_envelope(
        source=context.block(doi, item),
        subject_kind="work",
        subject_native_id=doi,
        label=title,
        attributes={
            "work_type": first_text(item.get("type"), default="scholarly_work"),
            "published": item.get("published"),
            "publisher": item.get("publisher"),
            "license_metadata": item.get("license", []),
            "abstract_persisted": False,
            "full_text_persisted": False,
        },
        identifiers=[
            identifier(
                scheme="doi",
                value=doi.replace("https://doi.org/", "").lower(),
                scope="global",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} DOI",
            )
        ],
        contributions=contributors,
        relationships=[],
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#doi-{doi}",
                literal=title,
                source_field="title",
            )
        ],
        raw_pointer=endpoint,
    )


def adapt_openalex_author(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    author_id = first_text(payload.get("id"))
    if not author_id:
        raise ValueError("OpenAlex author has no id")
    label = first_text(payload.get("display_name"), default=author_id)
    context = _context(
        source_id="openalex_api",
        payload=payload,
        endpoint=endpoint,
        retrieved_at=retrieved_at,
        terms_revision=SOURCE_POLICIES["openalex_api"]["terms_revision"],
        rights_state=SOURCE_POLICIES["openalex_api"]["rights_state_default"],
        observed_at=first_text(payload.get("updated_date"), retrieved_at),
    )
    ids = [
        identifier(
            scheme="openalex_author_id",
            value=author_id,
            scope="source",
            stability="stable",
            uniqueness="unique",
            evidence=f"{endpoint} id",
        )
    ]
    orcid = first_text(payload.get("orcid")).replace("https://orcid.org/", "")
    if orcid:
        ids.append(
            identifier(
                scheme="orcid",
                value=orcid,
                scope="global",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} orcid",
            )
        )
    return make_envelope(
        source=context.block(author_id, payload),
        subject_kind="person",
        subject_native_id=author_id,
        label=label,
        attributes={
            "works_count": payload.get("works_count"),
            "last_known_institutions": payload.get("last_known_institutions", []),
            "display_name_alternatives_persisted": False,
            "summary_stats_persisted": False,
        },
        identifiers=ids,
        contributions=[],
        relationships=[],
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#author-{author_id}",
                literal=label,
                source_field="display_name",
            )
        ],
        raw_pointer=endpoint,
    )


def adapt_openalex_work(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    work_id = first_text(payload.get("id"))
    if not work_id:
        raise ValueError("OpenAlex work has no id")
    title = first_text(payload.get("display_name"), payload.get("title"), default=work_id)
    context = _context(
        source_id="openalex_api",
        payload=payload,
        endpoint=endpoint,
        retrieved_at=retrieved_at,
        terms_revision=SOURCE_POLICIES["openalex_api"]["terms_revision"],
        rights_state=SOURCE_POLICIES["openalex_api"]["rights_state_default"],
        observed_at=first_text(payload.get("updated_date"), retrieved_at),
    )
    ids = [
        identifier(
            scheme="openalex_work_id",
            value=work_id,
            scope="source",
            stability="stable",
            uniqueness="unique",
            evidence=f"{endpoint} id",
        )
    ]
    doi = first_text(payload.get("doi")).replace("https://doi.org/", "")
    if doi:
        ids.append(
            identifier(
                scheme="doi",
                value=doi.lower(),
                scope="global",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} doi",
            )
        )
    contributors: list[dict[str, Any]] = []
    authorships = payload.get("authorships", [])
    if isinstance(authorships, list):
        for index, raw in enumerate(authorships):
            if not isinstance(raw, Mapping):
                continue
            author_record = raw.get("author") if isinstance(raw.get("author"), Mapping) else {}
            author_id = first_text(author_record.get("id"), default=f"{work_id}#author-{index}")
            label = first_text(author_record.get("display_name"), default=author_id)
            author_orcid = first_text(author_record.get("orcid")).replace("https://orcid.org/", "")
            agent_ids = [
                identifier(
                    scheme="openalex_author_id",
                    value=author_id,
                    scope="source",
                    stability="stable",
                    uniqueness="unique",
                    evidence=f"{endpoint} authorships[{index}].author.id",
                )
            ]
            identity_evidence = "source_native"
            if author_orcid:
                agent_ids.append(
                    identifier(
                        scheme="orcid",
                        value=author_orcid,
                        scope="global",
                        stability="stable",
                        uniqueness="unique",
                        evidence=f"{endpoint} authorships[{index}].author.orcid",
                    )
                )
                identity_evidence = "authority_identifier"
            contributors.append(
                contribution(
                    role="author",
                    agent_record=agent(
                        source_native_id=author_id,
                        label=label,
                        identifiers=agent_ids,
                    ),
                    evidence=f"{endpoint} authorships[{index}]",
                    order=index + 1,
                    identity_evidence=identity_evidence,
                )
            )
    return make_envelope(
        source=context.block(work_id, payload),
        subject_kind="work",
        subject_native_id=work_id,
        label=title,
        attributes={
            "work_type": first_text(payload.get("type"), default="scholarly_work"),
            "publication_date": payload.get("publication_date"),
            "open_access": payload.get("open_access"),
            "abstract_persisted": False,
            "full_text_persisted": False,
            "cited_by_count_persisted": False,
        },
        identifiers=ids,
        contributions=contributors,
        relationships=[],
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#work-{work_id}",
                literal=title,
                source_field="display_name|title",
            )
        ],
        raw_pointer=endpoint,
    )


def _openreview_content_value(content: Mapping[str, Any], key: str) -> Any:
    raw = content.get(key)
    if isinstance(raw, Mapping) and "value" in raw:
        return raw["value"]
    return raw


def adapt_openreview_note(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> dict[str, Any]:
    note_id = first_text(payload.get("id"), payload.get("forum"))
    if not note_id:
        raise ValueError("OpenReview note has no id/forum")
    content = payload.get("content") if isinstance(payload.get("content"), Mapping) else {}
    title = first_text(_openreview_content_value(content, "title"), default=note_id)
    modified_ms = payload.get("mdate") or payload.get("tcdate")
    context = _context(
        source_id="openreview_api",
        payload=payload,
        endpoint=endpoint,
        retrieved_at=retrieved_at,
        terms_revision=SOURCE_POLICIES["openreview_api"]["terms_revision"],
        rights_state=SOURCE_POLICIES["openreview_api"]["rights_state_default"],
    )
    authors = _openreview_content_value(content, "authors") or []
    author_ids = _openreview_content_value(content, "authorids") or []
    if isinstance(authors, str):
        authors = [authors]
    if isinstance(author_ids, str):
        author_ids = [author_ids]
    contributors: list[dict[str, Any]] = []
    if isinstance(authors, list):
        for index, label_raw in enumerate(authors):
            label = str(label_raw)
            profile_id = str(author_ids[index]) if isinstance(author_ids, list) and index < len(author_ids) else ""
            native_id = profile_id or f"{note_id}#author-{index}"
            ids = []
            identity_evidence = "name_only"
            if profile_id:
                ids.append(
                    identifier(
                        scheme="openreview_profile_id",
                        value=profile_id,
                        scope="source",
                        stability="stable",
                        uniqueness="unique",
                        evidence=f"{endpoint} content.authorids[{index}]",
                    )
                )
                identity_evidence = "source_native"
            contributors.append(
                contribution(
                    role="author",
                    agent_record=agent(
                        source_native_id=native_id,
                        label=label,
                        identifiers=ids,
                    ),
                    evidence=f"{endpoint} content.authors[{index}]",
                    order=index + 1,
                    identity_evidence=identity_evidence,
                )
            )
    venue_id = first_text(payload.get("venueid"), _openreview_content_value(content, "venueid"))
    relationships = []
    if venue_id:
        relationships.append(
            relationship(
                predicate="submitted_to",
                object_kind="organisation",
                object_native_id=venue_id,
                object_label=venue_id,
                evidence=f"{endpoint} venueid",
            )
        )
    license_value = _openreview_content_value(content, "license")
    return make_envelope(
        source=context.block(note_id, payload),
        subject_kind="work",
        subject_native_id=note_id,
        label=title,
        attributes={
            "work_type": "openreview_article",
            "venue_id": venue_id or None,
            "article_license": license_value,
            "metadata_license": "CC0-1.0",
            "modified_milliseconds": modified_ms,
            "abstract_persisted": False,
            "full_text_persisted": False,
            "reviews_or_comments_persisted": False,
            "profiles_persisted": False,
        },
        identifiers=[
            identifier(
                scheme="openreview_note_id",
                value=note_id,
                scope="source",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} id",
            )
        ],
        contributions=contributors,
        relationships=relationships,
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#note-{note_id}",
                literal=title,
                source_field="content.title",
            )
        ],
        raw_pointer=endpoint,
    )
