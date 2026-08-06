# Mapping identity_v3 onto an additive People Graph v3 schema

This lane deliberately does not depend on another branch. Its tables and Python
interfaces form a narrow compatibility seam that can map onto either current v2
or a future provenance-first v3 ontology.

## Conceptual mapping

| Lane-local surface | Future v3 concept | Integration rule |
| --- | --- | --- |
| `identity_v3_entity` | source entity / canonical-entity adapter | Preserve the source row ID; do not mint canonical identity from a label |
| `identity_v3_identifier` | identifier assertion + identifier definition | Join through scheme policy, source, observed time, validity, and literal evidence |
| `identity_v3_alias` | temporal alias/account-handle assertion | Keep stable account ID, `valid_from`, and `valid_to` |
| `identity_v3_attribute` | source observation / evidence-backed assertion | Do not promote attributes to unique identifiers |
| `identity_v3_candidate` | identity candidate claim | Preserve method version, evidence, conflicts, confidence, and review state |
| `identity_v3_decision` | identity decision/review lineage | Keep outcome, reviewer, rationale, active/reverted state |
| `identity_v3_generation` | named cluster projection run | Treat clusters as derived, reproducible output |
| `identity_v3_cluster_member` | canonical cluster membership + redirect | Resolve through a selected generation, never by destructive row rewrite |
| `identity_v3_audit_event` | data-quality/review event | Retain stable event ID and structured details |

A future v3 adapter should implement the same operations exposed by
`IdentityEngine`: upsert source entity, record identifier/alias/attribute,
generate candidates, accept/reject, resolve, undo, and audit. Query code should
consume `resolve_entity()` or an equivalent generation-scoped redirect lookup,
not read v2 `person.merged_into` as the only identity truth.

## Current v2 adapter

`identity_v3.adapters.import_v2()`:

1. copies every `person` row into the lane-local entity adapter;
2. reclassifies `external_ids` through the identifier registry;
3. links mutable GitHub login aliases to a stable GitHub numeric ID when present;
4. stores company/location/name/metrics as observations rather than identifiers;
5. imports legacy claims while quarantining non-eligible
   `shared_external_id` acceptances and transitive stable-ID conflicts;
6. leaves every v2 source row and content edge untouched.

The compatibility matcher still writes v2 `identity_claim` rows so existing
callers retain their interface, while the richer candidate and cluster state is
available in `identity_v3_*` tables.

## `pg-observation-0.1` mapping

`import_observation()` creates a deterministic **source-observation entity ID**
from `source_id`, subject kind, and source-native ID. The label is not part of the
ID, and the adapter rejects canonical-ID fields anywhere in the envelope.

- `source.*` supplies origin, native record context, observed time, and payload
  digest.
- `subject.kind`, `source_native_id`, and `label` populate the source entity.
- `subject.attributes` become timestamped attributes.
- `identifiers[]` are reclassified by the local registry. A source declaration
  that `company` is unique cannot override policy.
- aliases remain aliases; identifiers retain literal evidence and source time.
- contributions, relationships, evidence, and `raw_pointer` are retained as
  replayable envelope observations until a dedicated v3 table adapter exists.
- no envelope import creates an accepted identity decision or canonical cluster.

## Exact future seams

A schema integration PR can replace storage calls without changing candidate or
review policy by providing an adapter with these methods:

```python
upsert_entity(...)
record_identifier(...)
record_alias(...)
record_attribute(...)
generate_candidates(...)
accept_candidate(...)
reject_candidate(...)
resolve_entity(...)
undo_decision(...)
audit(...)
```

Required semantic compatibility:

- source observations survive merge/undo;
- identifier definitions remain explicit and deny-by-default;
- accepted decisions are reversible and carry review lineage;
- redirects are generation/version scoped;
- unique-identifier conflicts are checked across the full prospective cluster;
- publication/rights fields from the final v3 model flow through evidence and
  observation records rather than being dropped.

No in-place migration of a production SQLite asset is performed in this lane.
The preferred path is source reconstruction or additive table population,
validation, and a separately versioned cluster projection.
