# Compatibility adapter interface

## Contract

Every supported adapter exposes four read-only behaviors:

```python
iter_observations()        # pg-observation-0.1 dictionaries
iter_identity_decisions()  # separate decision objects; never folded into observations
export(path)               # deterministic NDJSON
capabilities()             # present, inferred, missing, and compatibility gaps
```

Adapters validate emitted observations before yielding them. SQLite adapters use `file:...?mode=ro`; source files are never mutated.

## Current v2 SQLite

`V2SQLiteAdapter` detects the current `person`, `person_content`, and `external_ids` tables and optionally projects `person_topic` and `identity_claim`.

- Legacy `person.person_id` values are encoded as `legacy-v2-person/...` source locators. They are not asserted as new canonical IDs.
- `identity_claim` rows, including accepted rows, are returned only by `iter_identity_decisions()`.
- `person_content` becomes a Work observation whose contribution retains `role`, contributor locator, source, observed time, title, score observation, and literal `meta_json`.
- `person_topic` remains namespaced by its source vocabulary/scheme.
- Known attribute-like rows in `external_ids`—including `real_name`, `company`, `location`, biography, and topics—are preserved under `subject.attributes.legacy_external_attributes`, never emitted as identifiers.
- Mutable aliases such as `github_login` and `x_handle` are source-scoped with mutable/unknown semantics.
- Stable source IDs such as `github_id`, YouTube channel ID, OpenAlex author ID, and DBLP PID receive source-stable semantics.
- Legacy rows do not contain exact source snapshots, terms revisions, deletion obligations, or rights state. The adapter therefore emits explicit `pending`/documented-unknown compatibility markers unless the caller supplies a `SourcePolicy`.

Example source policy file:

```json
{
  "gutenberg": {
    "snapshot_id": "gutenberg-2026-08-01",
    "terms_revision": "project-gutenberg-license-2026-08-01",
    "rights_state": "open_data",
    "retrieved_at": "2026-08-06T00:00:00Z"
  }
}
```

```bash
python3 -m integration adapt-sqlite people_v2.sqlite observations.ndjson \
  --source-policies source-policy.json \
  --decisions-output identity-decisions.json
```

## Book Library and source pilots

`BookLibraryObservationAdapter` and `NDJSONObservationAdapter` consume the same envelope. Book Works retain contributor roles rather than flattening a person into one global role. Source pilots retain source-native identifiers, snapshot/terms/rights metadata, payload hashes, and review-only identity evidence.

No NDJSON adapter produces accepted identity decisions.

## Future v3

`V3SQLiteAdapter` is capability-detecting rather than schema-guessing. It currently supports an additive table named `source_observation`, `source_observations`, `observation`, `observations`, or `source_record` with a full-envelope JSON column. It reports canonical, claim, and Work tables when detected, but does not guess their join or decision semantics. A future normalized v3 mapper can be added without changing observation import.

## Failure behavior

Unsupported schemas fail explicitly. Missing rights, malformed hashes, unsafe identifiers, private pointers, canonical IDs, or name-only identity relationships fail validation. Missing optional capabilities are reported as missing; they are not silently synthesized.
