# `pg-observation-0.1` mapping and invariants

The shared envelope is an observation contract, not a canonical ontology. Source adapters may disagree without losing the original payload digest or source-native IDs.

## Mapping

| Envelope field | Adapter responsibility |
| --- | --- |
| `envelope_version` | exactly `pg-observation-0.1` |
| `source.source_id` | versioned adapter/source namespace, such as `podcast_rss` |
| `source.snapshot_id` | content digest, source revision, or dated snapshot |
| `source.record_native_id` | stable source-local record ID when available |
| `source.observed_at` / `retrieved_at` | source truth time and collection time kept distinct |
| `source.terms_revision` | current reviewed terms/docs or documented publisher-specific unknown |
| `source.rights_state` | `public_metadata`, `open_data`, `restricted`, `discovery_only`, or `pending` |
| `source.payload_sha256` | SHA-256 of the replayable source payload/record, not the envelope |
| `subject` | source-native person, organisation, account, Work, event, venue, place, concept, or claim |
| `identifiers` | scheme, scope, stability, uniqueness, and literal evidence |
| `contributions` | Work/Event roles with source-native agents and evidence |
| `relationships` | typed source-observed links; no canonicalization |
| `evidence` | literal field locators, or explicitly marked model inference receipts |
| `raw_pointer` | source endpoint, fixture path, or content-addressed receipt |

## Enforced invariants

- No envelope or nested contribution may contain a People Graph canonical ID, cluster ID, merge target, or resolved identity.
- Names, display names, real names, companies, employers, locations, biographies, topics, usernames, and handles are never global unique identifiers.
- A YouTube channel, podcast show, or source account remains separate from its operating human or organisation.
- Source account IDs are source-scoped. Reuse across different source namespaces is an adapter conflict, not identity proof.
- Authority identifiers such as ORCID, VIAF, ISNI, and Wikidata may generate strong review candidates only when marked stable and unique.
- Explicit `sameAs` and official-site links generate review-only candidates. A shared name generates nothing.
- Every candidate retains its literal identifier evidence and source record. `automatic_acceptance` is always false in this lane.
- Model output must be marked as inference and include model name, version, and input digest. It cannot masquerade as a source field.
- Transcript/media relationships are pointers with `rights_gate: not_acquired`; payload bodies never enter the observation.

## Compatibility seam

The envelope can later map to an additive v3 source-observation schema. Current v2 consumers should treat it as an external NDJSON input and must not convert source-native IDs into `person.person_id` without the identity lane's explicit review and reversible decision path.
