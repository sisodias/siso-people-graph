# Engineering walkthrough: reconstructing Prompt 10

This walkthrough explains how the existing Prompt 10 branch was derived from the
source brief and how to verify or replace it. It complements the decision log;
it does not duplicate private scratch work.

## 1. Inputs and fixed boundaries

The implementation had four authoritative inputs:

1. the verbatim Prompt 10 brief in `prompt-10-source.md`;
2. current-main People Graph behavior and its provenance/identity principles;
3. the shared `pg-observation-0.1` contract in the parallel-slam brief;
4. current official source/API/terms documentation listed in `source-ledger.md`.

The lane owns only:

- `sources/software/**`;
- `sources/ai/**`;
- `tests/sources_software_ai/**`;
- `docs/source-methods/software-ai/**`;
- `docs/handoffs/software-ai-pilot.md`.

It deliberately does not edit the schema, identity engine, loaders, query layer,
claims layer, root configuration, README, or database assets.

## 2. Translate prose into executable invariants

The brief was decomposed into invariants before source-specific code:

- every row is versioned as `pg-observation-0.1`;
- every row carries source snapshot/native ID, observation/retrieval timestamps,
  terms revision, rights state, payload digest, evidence, and raw pointer;
- identifiers declare scope, stability, uniqueness, and literal evidence;
- names, real names, companies, locations, biographies, and bios are never IDs;
- canonical IDs, merge targets, rank scores, and universal scores are forbidden;
- contribution agents are typed as person, account, or organisation;
- relationships have predicates, typed objects, observed time, and evidence;
- mutable handles/path names never replace stable source identifiers;
- metrics are timestamped observations;
- deterministic export is independent of adapter iteration order;
- tests perform no network I/O.

`sources/software/envelope.py` is the enforcement point. New adapters must not
weaken it locally.

## 3. Source portfolio and why each source exists

The bounded portfolio is complementary rather than redundant:

| Source | What it contributes | Why it is not sufficient alone |
| --- | --- | --- |
| GitHub REST/GraphQL | current account, organisation, repository, release, owner/contributor state and numeric IDs | broad enrichment is API-costly; current state does not provide full event history |
| GH Archive | timestamped public GitHub event evidence | historical events do not prove current availability or identity |
| PyPI | Python package/release metadata, hashes, dependencies, roles, project URLs | free-text authors are unsafe identity evidence; per-project JSON is costly at full scale |
| crates.io/Cargo index | crate versions, checksums, yank state, dependencies; bounded owners | index does not by itself identify humans across platforms |
| ecosyste.ms | normalized cross-registry packages/repos/dependencies, including npm coverage | may lag or disagree with registry-native metadata |
| Software Heritage | intrinsic archive identifiers and origin/revision verification | public API is unsuitable for broad discovery; archival presence is not a license |
| Hugging Face Hub | model, dataset, Space, account/organisation, revision and typed artifact links | namespaces are mutable and payload rights are item-specific |

Direct npm collection was deferred because the normalized source covers the
pilot’s required fields. This is a measured-gap decision, not a permanent ban.

## 4. Adapter pipeline

The pipeline is intentionally simple:

```text
fixture JSON
  -> source adapter
  -> make_envelope(raw_record, source receipt, subject, IDs, edges)
  -> validate_envelope
  -> deterministic sort and canonical JSON
  -> NDJSON + descriptive metrics
  -> manifest digest and offline tests
```

`payload_sha256` hashes the replayable raw fixture record, not the normalized
envelope. That lets a reviewer prove which input produced an observation even if
normalization changes later.

### GitHub and GH Archive

- Account records use numeric account ID and node ID as stable source-scoped
  identifiers; login is mutable.
- Previous logins become `renamed_from` relationships with valid time.
- Repository records use numeric repository ID and node ID; `owner/name` is
  mutable.
- Owner and contributors become typed contribution edges.
- Transfers become `transferred_from` relationships; dependencies and SWHIDs
  become typed links.
- Releases are separate Works linked by `version_of`.
- GH Archive events are Events linked to actor accounts and repository Works.

### Packages and registries

- Package coordinates/PURLs identify package Works, not maintainers.
- Versioned PURLs and checksums identify releases/artifacts where supplied.
- Owners, maintainers, and publishers are contributions.
- Dependencies are `depends_on` relationships with requirement/environment
  attributes.
- Yank, abandonment, and archive state remain source observations.
- ecosyste.ms observations do not overwrite registry-native observations.

### Software Heritage

- SWHIDs are represented as global stable unique identifiers for archive
  objects.
- Archive objects link to known origins/Works through `archives` relationships.
- The adapter stores metadata and locators, not source payloads.

### Hugging Face

- Accounts and organisations remain distinct subjects.
- Models, datasets, Spaces, and revisions remain distinct Work types.
- Revision SHAs are stable content-history identifiers; namespace paths and
  handles are mutable.
- `trained_on`, `uses_model`, and `uses_dataset` preserve the artifact graph.
- Cards/licenses/metrics remain source observations; no weights or datasets are
  downloaded.

## 5. Worked transformation: repository transfer

The adversarial GitHub fixture represents repository numeric ID `1001` under two
full names at different observation times.

1. Both raw records retain their own payload hash and raw pointer.
2. Both emit `github_repository_id=1001` as stable/source/unique evidence.
3. Each full name is emitted as a mutable identifier.
4. Ownership is represented on a `repository_owner` contribution.
5. The later observation records `transferred_from` with valid time and literal
   evidence.
6. Both observations survive export; no canonical person or organisation is
   created.

The test `test_repository_transfer_uses_stable_repository_id` proves continuity
of the source-native repository while ownership and path change.

## 6. Conflict handling

The fixture intentionally gives `pkg:pypi/vectorforge` two non-empty license
values from PyPI and ecosyste.ms. `compute_metrics` groups package observations
by source-native ID, detects distinct license values, and records:

- each source/value pair;
- the distinct values;
- `resolution: preserve_conflict_for_review`.

This metric is not adjudication. A production schema must retain both source
observations and add a separate reviewed decision if one value becomes the
published projection.

## 7. Metric derivations

The committed metrics are descriptive:

- `record_count`: number of validated envelopes;
- `source_count`: distinct source IDs;
- `stable_unique_identifiers`: distinct `(scheme, value)` pairs whose declared
  stability is stable and uniqueness is unique, including nested contribution
  agent identifiers;
- `identifier_observations`: all identifier-shaped mappings, including repeated
  evidence receipts;
- `contribution_edges` and `relationship_edges`: explicit edge counts grouped by
  role/predicate;
- `metric_observations`: timestamped metric objects;
- `cross_platform_identity_evidence_receipts`: literal GitHub numeric IDs on
  non-GitHub source records, without merge semantics;
- `license_coverage`: Works with a declared source-observed license / all Works;
- `rights_coverage`: records with terms revision and a non-pending,
  non-restricted rights state / all records;
- archived/abandoned Work counts and temporal relationship counts;
- source conflicts as described above.

They do not measure production accuracy, recall, throughput, freshness, or API
cost. Those require an online cohort and reviewed ground truth.

## 8. Determinism

`canonical_json` uses UTF-8-preserving JSON, sorted keys, fixed separators, and
rejects NaN. `write_ndjson` sorts records by source ID, source record-native ID,
subject source-native ID, and payload digest. Tests export both forward and
reversed input order and compare bytes.

The implementation run recorded:

- 31 validated envelopes;
- 7 source adapters;
- 23 Works, 4 accounts, 2 organisations, and 2 events;
- 36 distinct stable unique identifiers;
- 98 identifier observations;
- 30 contribution edges and 35 relationship edges;
- 43 timestamped metric observations;
- 8 literal cross-platform GitHub numeric-ID evidence receipts;
- 2 temporal rename/transfer relationships;
- 3 archived and 3 abandoned Works;
- 1 preserved source conflict;
- 100% fixture terms/rights coverage and 91.3% declared-license coverage;
- 0 network calls, canonical merges, or universal scores;
- logical NDJSON SHA-256
  `f1e5b923f22b6e94f9102bda2abc4c33f0bfd3bd8ed03b8fc903dee745b5780e`.

These numbers describe the synthetic fixture pilot only.

## 9. Reproduction commands

From repository root:

```bash
PYTHONPATH=. python -m unittest discover -s tests/sources_software_ai -v

PYTHONPATH=. python -m sources.software.pilot export \
  --fixtures tests/sources_software_ai/fixtures \
  --out /tmp/software-ai.ndjson \
  --metrics-out /tmp/software-ai-metrics.json

PYTHONPATH=. python -m sources.software.pilot validate /tmp/software-ai.ndjson
PYTHONPATH=. python -m sources.software.pilot metrics --path /tmp/software-ai.ndjson
python -m compileall -q sources tests
sha256sum /tmp/software-ai.ndjson
```

Expected implementation-run result: 18 tests passed, 31 records validated, and
the logical digest above. The committed `pilot-manifest.json` fingerprints every
fixture and the logical output. A changed digest is not automatically an error;
it is a contract change that must be explained and reviewed.

## 10. Failure modes and honest limitations

- A stable platform account ID does not prove permanent human control.
- Package coordinates can be transferred, deleted, or reused.
- Public metrics are volatile and gameable.
- Maintainer APIs can be incomplete.
- Normalized sources can lag or conflict with registries.
- Source terms and API behavior change; production receipts must record the exact
  retrieval-time revision.
- Software Heritage presence is not permission to redistribute code.
- Hugging Face metadata, cards, files, weights, and datasets can carry different
  access and license states.
- Historical event archives do not prove current source availability.
- Synthetic fixtures do not establish production coverage, precision, recall,
  lag, cost, or deletion compliance.
- No accepted cross-platform identity precision is reported because the lane
  emits evidence receipts only and has no reviewed match/non-match set.

## 11. Safe extension protocol

To add a source:

1. document official access, IDs, terms, rights, update/removal semantics, cost,
   promote criteria, and kill criteria;
2. add a tiny public-safe synthetic fixture;
3. retain source snapshot/revision and raw pointers;
4. emit source-native subjects only;
5. annotate every identifier’s scope/stability/uniqueness/evidence;
6. keep roles on contributions and history/dependencies on relationships;
7. timestamp all metrics;
8. preserve conflicts;
9. add negative and adversarial tests;
10. regenerate and review metrics/manifest changes;
11. do not add canonical IDs or merge decisions in this lane.

## 12. Highest-value review questions

A reviewer should challenge these first:

- Are any declared stable IDs actually mutable or reused within their stated
  scope?
- Can the future schema preserve multiple observations, raw locators, valid time,
  conflict state, tombstones, and rights suppression without loss?
- Are deletion/attribution obligations implementable at projected scale?
- Does the recommended source order maximize strong joins and decision value per
  request, rather than only row count?
- Which synthetic cases need public-safe production-derived red-team fixtures
  before promotion?
