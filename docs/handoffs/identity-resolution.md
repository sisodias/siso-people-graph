# Parallel handoff: safe identity resolution

## Scope

Parallel lane: Identity resolution  
Branch: `pg/identity-resolution-parallel-20260806`  
Base inspected at launch: `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
Open pull requests visible at launch: none

This lane adds a self-contained, evidence-calibrated identity module; fixes the
current matcher so only registry-eligible identifiers can drive
`shared_external_id`; makes GitHub profile enrichment observation-oriented and
replayable; and provides reversible canonical cluster generations with CLI and
offline adversarial tests.

## Changed paths

- `identity_v3/**`
- `loaders/match_identities.py`
- `loaders/enrich_owners.py`
- `tests/identity_v3/**`
- `docs/handoffs/identity-resolution.md`

No core schema, build loader, query surface, README, or root configuration is
changed.

## Commands

```bash
PYTHONPATH=. python3 -m compileall -q \
  identity_v3 loaders/match_identities.py loaders/enrich_owners.py tests/identity_v3
PYTHONPATH=. python3 -m unittest discover \
  -s tests/identity_v3 -p 'test_*.py' -v
PYTHONPATH=. python3 tests/identity_v3/measure_precision.py
python3 -m identity_v3 registry
python3 -m identity_v3 propose --db people_v2.sqlite
python3 loaders/match_identities.py --graph people_v2.sqlite --apply \
  --accept shared_external_id
python3 loaders/enrich_owners.py --graph fixture.sqlite \
  --fixture tests/identity_v3/fixtures/github_profiles.json
```

## Tests

Offline result on 2026-08-06:

- 15 unit/integration tests passed.
- Automatic candidates: 4/4 labeled true, 0 labeled false; 2 additional
  deliberately inconsistent conflict-fixture pairs were excluded from labeled
  precision.
- Automatic policy: 5 accepted, 1 transitive merge blocked because it would
  create conflicting ORCIDs; final cluster audit passed.
- Review-only candidates: 1/6 true on the deliberately adversarial fixture.
- Enrichment rerun fetched zero records after present and absent receipts were
  recorded; canonical name, rank, and build timestamp remained unchanged.

These are synthetic fixture measurements, not production precision estimates.

## Assumptions

- Current v2 `person_id` values identify source/canonical rows that must survive
  every identity decision and undo.
- GitHub numeric account ID and other registry-approved authority IDs are strong
  candidate evidence, subject to pair and transitive conflict checks.
- Mutable handles and all human-readable profile fields are observations, not
  globally unique identifiers.
- A deterministic canonical row preference is useful for redirects but does not
  declare that row intrinsically more truthful.
- Existing callers may still require v2 `identity_claim` and `external_ids`
  compatibility during transition.

## Compatibility seams

- `IdentityEngine` exposes inspect, propose, review, accept, reject, resolve,
  undo, and audit operations independent of the future schema.
- `import_v2()` maps current people, external fields, and legacy claims without
  destructive merge.
- `import_observation()` maps `pg-observation-0.1` without assigning a canonical
  ID and rejects canonical-ID fields in the envelope.
- `identity_v3/V3_MAPPING.md` specifies the table and interface mapping for an
  additive v3 schema.
- Query integration should read the latest cluster generation or an equivalent
  adapter, while continuing to expose source rows and ambiguity.
- Build integration should initialize the additive DDL and validate cluster
  conflicts, but should not mutate a production database in place.

## Known risks

- Production precision is unmeasured; release gating needs stratified manual
  review across methods, source pairs, scripts/languages, and entity kinds.
- Authority IDs can contain upstream errors, redirects, splits, or concepts that
  are not exactly one natural person.
- The v2 compatibility table still stores non-identifiers such as company and
  location in `external_ids`. This lane prevents them from matching, but a future
  schema should store them only as observations.
- A manual reviewer can use `--allow-conflicts`; this is intentionally explicit
  and will make `audit()` fail until the contradiction is resolved or undone.
- Canonical selection policy may need adjudication with the schema/query lanes.
- The enricher refines only `kind='unknown'` from GitHub's account type for
  backward compatibility. The source value is also retained as an observation.

## Data and rights notes

- Tests use fabricated people and fabricated GitHub profile payloads only.
- No production SQLite database, bulk corpus, credential, token, private path,
  personal note, or network recording is committed.
- Network access is injectable; all tests replay tiny local fixtures.
- The implementation stores metadata/evidence receipts and payload digests, not
  profile-page or content corpora.
- Source-specific retention and deletion obligations remain the responsibility
  of the build/source governance lanes; this module preserves source and
  observation provenance needed to apply them.

## Suggested merge considerations

1. Merge or evaluate this lane before bulk ingestion that could generate
   `shared_external_id` claims from unclassified `external_ids` values.
2. Keep the registry deny-by-default when reconciling with schema-v3 identifier
   definitions; do not broaden automatic eligibility by migration shortcut.
3. Have the query lane surface candidate state, cluster generation, redirect,
   conflicts, and source rows separately.
4. Have the build lane run the offline identity tests and `identity_v3 audit` as
   release gates.
5. Resolve any competing canonical-selection policy through an explicit adapter
   or decision record rather than rewriting source IDs.
6. Regenerate a production identity projection only from declared source inputs;
   do not copy the synthetic fixture measurements into production claims.
