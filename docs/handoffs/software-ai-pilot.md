# Handoff: software and AI creator pilot

## Scope

A bounded, evidence-first source lane for GitHub/GH Archive, ecosyste.ms,
PyPI, crates.io, Software Heritage, and Hugging Face Hub. The lane emits
replayable `pg-observation-0.1` envelopes from synthetic fixtures and measures
identifier, contribution, relationship, rights, license, temporal, archival,
and conflict coverage.

Direct npm collection is deferred; npm is represented through ecosyste.ms.
No production crawl, canonical entity resolution, or ranking was added.

## Changed paths

- `sources/software/**`
- `sources/ai/**`
- `tests/sources_software_ai/**`
- `docs/source-methods/software-ai/**`
- `docs/handoffs/software-ai-pilot.md`

No schema, loader, README, or database path outside this lane was modified.

## Commands

```bash
PYTHONPATH=. python -m unittest discover -s tests/sources_software_ai -v

PYTHONPATH=. python -m sources.software.pilot export \
  --fixtures tests/sources_software_ai/fixtures \
  --out /tmp/software-ai.ndjson \
  --metrics-out /tmp/software-ai-metrics.json

PYTHONPATH=. python -m sources.software.pilot validate /tmp/software-ai.ndjson
PYTHONPATH=. python -m sources.software.pilot metrics --path /tmp/software-ai.ndjson
```

## Tests

Eighteen standard-library `unittest` cases cover:

- envelope validation and deterministic NDJSON;
- committed manifest/metrics replay and fixture hash verification;
- rejection of canonical/rank/merge fields;
- rejection of names, companies, locations, and bios as identifiers;
- Unicode-preserving JSON;
- no-network fixture replay;
- GitHub rename and repository transfer continuity;
- organisation entity typing;
- package maintainer/contributor edge semantics;
- cross-registry dependency edges and PURLs;
- SWHID stability;
- distinct model/dataset/Space types and links;
- timestamped source metrics;
- literal cross-platform identity evidence without merges;
- conflict preservation;
- archived and abandoned Work cases;
- expected measured pilot counts.

Latest local result before publication: 18 tests passed.

## Assumptions

- Numeric GitHub account/repository IDs and GitHub node IDs are the strongest
  source-scoped continuity keys available in the bounded GitHub records.
- Registry coordinates/PURLs identify Works, not people.
- Package owner/maintainer rows and repository contributors are contribution
  relationships, not aliases.
- Hugging Face repository paths and account handles are mutable; revision SHAs
  are stable content-history identifiers.
- SWHIDs identify archived software objects, not a redistribution license.
- Every production observation will carry a retrieval receipt, terms revision,
  rights state, payload hash, and raw locator equivalent to the fixture contract.

## Compatibility seams

The lane does not write the current `people_schema_v2.sql`. Integration should
consume NDJSON and map only these stable seams:

- `subject.kind` and `subject.attributes.work_type` for entity/work typing;
- `identifiers[]` with explicit stability/uniqueness metadata;
- `contributions[]` for role-bearing creator/maintainer/owner edges;
- `relationships[]` for dependency, version, source-repository, archival,
  temporal, and AI artifact links;
- `source` plus `raw_pointer` for provenance and replay;
- timestamped `subject.attributes.metrics` as observations, never rank inputs.

An ontology/core PR should define how to persist observation receipts and
conflicts before accepting this lane’s data. It should not map
`subject.source_native_id` directly to a canonical person ID.

## Known risks

- A numeric source ID can be stable inside a platform but still represent an
  account whose human/organisation control changes.
- Registry project names can be deleted, transferred, or reused; PURLs identify
  package coordinates, not immutable maintainers.
- Maintainer/team APIs vary in completeness and may expose less than registry
  administrators can see.
- Public metrics are volatile and gameable; they are useful only with timestamps
  and source context.
- ecosyste.ms normalization can lag or disagree with registry-native metadata.
- Hugging Face card metadata may be absent, inconsistent, gated, or licensed
  differently from files/weights/datasets.
- Software Heritage’s public API is not a bulk extraction channel.
- Share-alike and source-specific terms require downstream attribution and
  deletion/suppression procedures.
- The current fixtures are synthetic; production accuracy, coverage, lag, and
  API cost remain unmeasured.

## Data and rights notes

All committed fixture identities, projects, repositories, packages, metrics,
and conflicts are invented. No production personal data or copyrighted payload
is included. Source method cards record reviewed terms/policy references as of
2026-08-06, but production collection must re-check them and record exact
retrieval-time revisions.

The pilot stores metadata and locators only. It does not download repository
contents, package archives, model weights, datasets, or gated/private content.
Item-level licenses remain source observations and may conflict.

## Suggested merge considerations

1. Review `pg-observation-0.1` with ontology/core owners, especially conflict,
   tombstone, and provenance persistence.
2. Keep this PR isolated from concurrent core-schema work; it changes only owned
   paths and can merge independently.
3. Decide whether the repository wants a production dependency policy for
   `huggingface_hub`, Package-URL tooling, and optional GitHub clients.
4. Run an online cohort only after terms/rate-limit receipts, cache policy,
   deletion handling, and source-specific kill criteria are approved.
5. Scale in this order: ecosyste.ms discovery, bounded GitHub numeric-ID/HF
   enrichment, PyPI/Cargo index deltas, GH Archive time windows, then SWH point
   verification.
6. Do not add direct npm crawling until a measured gap justifies it.
7. Do not merge any inferred identity claims from this lane without reviewed
   match/non-match ground truth and reversible identity-policy ownership.
