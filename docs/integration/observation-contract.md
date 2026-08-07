# `pg-observation-0.1` source observation contract

## Purpose

`pg-observation-0.1` is the shared exchange seam for independent source, Book Library, schema, build, query, identity, and claims lanes. It represents what one source said at one recorded snapshot. It is not a canonical entity, cluster, redirect, merge command, or ranking result.

The normative executable validator is `integration/contract.py`. `integration/pg_observation_0_1.schema.json` is a structural companion; semantic rules such as recursive canonical-ID rejection, handle mutability, name-only identity checks, and payload verification are enforced by Python.

## Required envelope

Every NDJSON line is one object with these required fields:

| Field | Required semantics |
| --- | --- |
| `envelope_version` | Exactly `pg-observation-0.1`. |
| `source.source_id` | Stable source namespace, not a People Graph entity ID. |
| `source.snapshot_id` | Exact source snapshot, release, query receipt, export batch, or documented legacy gap. |
| `source.record_native_id` | Native record locator inside that source snapshot. |
| `source.observed_at` | When the represented fact was true or published, with timezone. |
| `source.retrieved_at` | When the payload was retrieved, with timezone. |
| `source.terms_revision` | Terms/license revision or an explicit documented-unknown marker. |
| `source.rights_state` | `public_metadata`, `open_data`, `restricted`, `discovery_only`, or `pending`. |
| `source.payload_sha256` | SHA-256 of the exact retained payload or compatibility row receipt. |
| `subject.kind` | Source-observed kind such as `person`, `organisation`, `account`, `work`, or `event`. |
| `subject.source_native_id` | Native subject locator; never a newly assigned canonical People Graph ID. |
| `subject.label` | Literal source label for display, never an identity key by itself. |
| `subject.attributes` | Literal source attributes. Names, company, location, biography, topics, and counts belong here. |
| `identifiers` | Identifier observations with explicit `scope`, `stability`, `uniqueness`, and literal evidence. |
| `contributions` | Work/event contributions with roles and source-native contributor locators. |
| `relationships` | Source relationships. Identity-like relationships must remain observed/proposed/review-only. |
| `evidence` | Receipts, methods, limitations, and provenance. |
| `raw_pointer` | Repository-relative fixture path, public locator, opaque SQLite locator, or content-addressed receipt. Private absolute paths are forbidden. |

## Identity invariants

1. Observation records do not carry `canonical_id`, `canonical_person_id`, `people_graph_id`, `cluster_id`, redirects, `merged_into`, or equivalent recursive fields.
2. Observation records do not contain automatic merge directives.
3. A name, normalized name, real name, company, employer, location, biography, or topic is an attribute, never an identifier scheme.
4. Handles and logins are source-scoped mutable aliases. They cannot be declared global, stable, or universally unique.
5. Identity-like relationships such as `same_as` remain `observed`, `proposed`, `needs_review`, or `review_only`; accepted canonical decisions live in a separate decision stream.
6. Name-only, exact-name, normalized-name, or surname-initial evidence is insufficient for an identity relationship.
7. Source-native fields named `person_id` or `entity_id` may be retained inside attributes. The ban targets newly assigned canonical People Graph identity, not literal source data.

## Identifier semantics

| Example | Scope | Stability | Uniqueness | Notes |
| --- | --- | --- | --- | --- |
| ORCID, VIAF, ISNI, Wikidata, ROR | Global | Stable | Unique | Still requires literal source evidence and review of source errors. |
| GitHub numeric account ID, YouTube channel ID, OpenAlex author ID | Source | Stable | Unique within source | Source deletion/reassignment policy still matters. |
| GitHub login, X handle, Reddit user, Mastodon/Bluesky handle | Source | Mutable | Unknown | Alias only; rename and reuse must not split or fuse canonical people silently. |
| Name, real name, company, location, biography, topic | Not an identifier | Not applicable | Non-unique | Preserve under attributes/evidence only. |

## Rights and payload integrity

The contract does not infer permission from public accessibility. Every record declares a rights state and a terms revision. Restricted or discovery-only records can describe a source without committing its payload. The payload hash allows replay and tamper detection; when `--payload-root` is provided, the validator resolves repository-relative pointers and verifies the exact bytes.

```bash
python3 -m integration validate \
  tests/integration_parallel/fixtures/valid_observations.ndjson \
  --payload-root .
```

## Versioning

Optional source-specific fields may be added without changing `0.1` when they do not alter existing semantics. A breaking change to required fields, identity rules, rights interpretation, digest meaning, or contribution semantics requires a new envelope version and an explicit adapter. Producers must not silently reinterpret a `0.1` field.
