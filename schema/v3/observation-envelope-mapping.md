# `pg-observation-0.1` import mapping

The interim envelope is accepted **without field changes**. It is an observation
contract, not a canonical ontology. Importing one record must not create an
`entity`, `identity_candidate`, `identity_decision`, cluster, redirect, assertion,
or projection.

## Receipt and validation

The complete JSON record is stored in `observation_envelope_receipt.payload_json`.
The table verifies:

- `envelope_version` is exactly `pg-observation-0.1`;
- source ID and record-native ID agree with the indexed receipt columns;
- the payload is valid JSON;
- top-level or subject-level canonical IDs are absent;
- the receipt is append-only and content-addressed by SHA-256.

The importer should additionally verify that the receipt SHA-256 equals the
canonical UTF-8 serialization chosen by the build manifest. The database checks
shape and digest syntax; the importer checks digest bytes.

## Field mapping

| Envelope field | v3 destination | Notes |
| --- | --- | --- |
| `envelope_version` | `observation_envelope_receipt.envelope_version` | Exact value only. |
| `source.source_id` | `source.source_id`, receipt `source_id` | Source registry row must already exist or be created from a reviewed source manifest. |
| `source.snapshot_id` | `source_snapshot.snapshot_id` | The source-native revision, terms, acquisition, digest, and deletion policy live on the snapshot. |
| `source.record_native_id` | receipt and `source_observation.record_native_id` | Never treated as globally unique. |
| `source.observed_at` | `source_observation.observed_at` | Time the source says the record/fact was true. |
| `source.retrieved_at` | `source_observation.retrieved_at`; snapshot retrieval time | Retrieval and observation time remain distinct. |
| `source.terms_revision` | `source_snapshot.terms_revision` | Import fails when the manifest and envelope disagree. |
| `source.rights_state` | snapshot and observation `rights_state` | Envelope states map directly; no inference from public visibility. |
| `source.payload_sha256` | `source_observation.payload_sha256` | Digest of replayable source payload or record, not necessarily the envelope receipt digest. |
| `subject.kind` | `source_observation.subject_kind` | Source-observed kind; not a canonical entity decision. |
| `subject.source_native_id` | `source_observation.subject_native_id` | Scoped to the source snapshot. |
| `subject.label` | `source_observation.label` | Preserved exactly; may later support an alias or canonical-label decision. |
| `subject.attributes` | `source_observation.attributes_json` | Names, companies, locations, biographies, topics, metrics, and handles stay attributes unless a reviewed typed mapping says otherwise. |
| `identifiers[]` | `observation_identifier` | Scheme, value, scope, stability, uniqueness, and literal evidence are retained per record. The scheme must have an `identifier_scheme` definition before canonical use. |
| `contributions[]` | `observation_contribution` | Source-native Work/contributor IDs, role, order, time, attributes, and literal evidence; no canonical Work or person ID is assigned. |
| `relationships[]` | `observation_relationship` | Predicate namespace and source-native endpoints are retained. Canonical temporal relationships are a later evidenced step. |
| `evidence[]` | `observation_evidence_item` | Model output must set `generated_by_model=1` with model/version/input digest. |
| `raw_pointer` | `source_observation.raw_pointer` | Tiny fixture path, source locator, or content-addressed receipt. Full payloads remain outside Git unless public-safe and tiny. |

## Import sequence

1. Validate the source manifest, rights/terms revision, and digest bytes.
2. Insert or verify `source` and `source_snapshot`.
3. Insert the immutable envelope receipt.
4. Insert one or more `source_observation` rows when one record contains several
   source-native subjects.
5. Insert identifier, contribution, relationship, and evidence child rows.
6. Emit an `observation_status_event(status='active')`.
7. Stop. Canonicalization is a separate reviewed process.

## Canonicalization seam

A later identity or Work-resolution service may create opaque `entity` IDs and
link accepted identifiers, aliases, Works, assertions, or relationships to the
source observations. That service must preserve all source rows, record its
method/version/evidence, and use append-only decisions. Names, companies,
locations, topics, biographies, handles, popularity metrics, and model labels
never become identity evidence merely because they are present in the envelope.
