# Parallel handoff — living creators/media pilot

## Scope

Add a self-contained living-creator and media observation lane for `sisodias/siso-people-graph`. The lane maps bounded saved payloads from RSS/Podcasting 2.0, Podcast Index, YouTube, Open Library, Crossref, OpenAlex, OpenReview, pretalx schedules, and explicit public-page JSON-LD to `pg-observation-0.1`. It proposes evidence-only identity candidates and deterministic cohort/metrics artifacts. It does not perform network collection, canonical identity resolution, production ingestion, or media/full-text acquisition.

## Changed paths

- `sources/creators/**`
- `sources/media/**`
- `tests/sources_creators_media/**`
- `docs/source-methods/living-creators/**`
- `docs/handoffs/living-creators-pilot.md`

No core schema, existing loader, query code, identity implementation, README, root configuration, or production database is changed.

## Commands

```bash
PYTHONPATH=. python3 -m unittest discover -s tests/sources_creators_media -v

PYTHONPATH=. python3 -m sources.media.pilot export-fixtures \
  --fixture-dir tests/sources_creators_media/fixtures \
  --out-dir /tmp/living-creators-pilot \
  --retrieved-at 2026-08-06T15:00:00Z \
  --target-size 250

PYTHONPATH=. python3 -m sources.media.pilot validate \
  /tmp/living-creators-pilot/observations.ndjson

PYTHONPATH=. python3 -m sources.media.pilot policies \
  --out /tmp/source-policies.json
```

## Tests

- 18 offline unit tests pass.
- 16 fixture observations validate against `pg-observation-0.1`.
- 9/9 fixture source IDs have executable refresh/removal/retention policies.
- Every bridge candidate contains literal identifier evidence and source record receipts.
- Names and non-unique attributes do not create candidates.
- YouTube channels remain account observations, separate from humans/organisations.
- No transcript/media/full-text payload is retained.
- Cohort selection is deterministic and name-only seeds are rejected.

## Assumptions

- Production collectors save source payloads outside Git and invoke these pure adapters.
- A current People Graph GitHub seed export and current modern-author seed export will be supplied later; the checked-in manifest is honestly fixture-only at 10/250.
- Source terms are re-verified at collection time. The source-policy registry records the reviewed 2026-08-06 boundary but cannot freeze external terms.
- Source-native timestamps and identifiers are preserved even when sources disagree.

## Compatibility seams

- NDJSON output is the unchanged `pg-observation-0.1` envelope and assigns no canonical ID.
- `sources.creators.bridges.propose_bridges()` produces a review queue consumable by the identity lane; it never writes accepted decisions.
- `sources.creators.cohort.build_manifest()` accepts future v2/v3 export rows once converted to the documented source-native seed contract.
- Source policy export can feed build/integration validation without importing adapter internals.
- Future v3 import should map source records, identifiers, Works, contributions, relationships, and evidence separately; current v2 `person_id` must not be generated from labels.

## Known risks

- The fixture parser surface is intentionally bounded; malformed real-world RSS/Atom and JSON-LD will need a production parser/library review.
- The 250-person production cohort was not collected in this lane because no current source-native seed snapshot/release asset was available in the execution environment. Fixture metrics are not production coverage or precision estimates.
- `sameAs` and official-site links can be stale, redirected, controlled by organisations, or point to a shared property; they remain review-only.
- Podcast Index API retention is cache-header bounded under the reviewed terms; accidental permanent caching is a release blocker.
- YouTube terms/quota/storage policy can change and must be rechecked immediately before collection.
- Event-publisher terms vary even when schedule data is exposed through pretalx.

## Data and rights notes

- Git contains only tiny invented/public-safe fixtures and generated fixture summaries.
- No production SQLite database, API credential, private path, personal note, transcript, audio, video, PDF, article/newsletter body, book text, or bulk source payload is committed.
- Metadata/evidence pointers are the default. Rights state, terms revision, payload digest, and raw pointer are mandatory.
- Reddit, X, LinkedIn, Goodreads, Google Scholar, and similar sources remain discovery-only and are not implemented as persistent adapters.

## Suggested merge considerations

- Merge independently; no schema or identity PR is required.
- Preserve the exclusive paths above when resolving parallel branches.
- Integration should validate the envelope and source-policy registry before wiring any importer.
- Do not add an automatic identity-acceptance path during conflict resolution.
- Before a production pilot, generate a fresh 250-person source-native cohort, manually review a stratified candidate sample, and rerun terms/rights verification.
