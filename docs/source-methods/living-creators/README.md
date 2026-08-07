# Living creators and media observation pilot

This lane adds deterministic, offline adapters for the populations that should bridge the current People Graph's books, code, papers, podcasts, talks, video, conferences, and public author pages. It emits only `pg-observation-0.1` source observations. It never assigns a People Graph ID, accepts an identity match, downloads media, or writes a production database.

## What is implemented

The adapters cover a bounded combination of:

- publisher RSS/Atom and Podcasting 2.0 person/transcript metadata;
- Podcast Index API responses under a cache-bounded restricted policy;
- YouTube Data API channel and video metadata, with channels represented as accounts rather than humans;
- Open Library authors, works, and editions;
- Crossref works, OpenAlex authors/works, and OpenReview public notes;
- public pretalx schedule exports;
- JSON-LD/schema.org from an explicitly supplied public page.

Every emitted record carries a source snapshot/native ID, observation and retrieval times, a terms revision, rights state, source-payload digest, source-native subject, typed identifiers, contribution roles, relationships, literal evidence, and raw pointer. The validator rejects canonical identity fields recursively and rejects names, companies, locations, biographies, topics, and handles as global unique identifiers.

## Commands

Run all offline fixtures and produce observations, a review queue, a cohort manifest, and metrics:

```bash
PYTHONPATH=. python3 -m sources.media.pilot export-fixtures \
  --fixture-dir tests/sources_creators_media/fixtures \
  --out-dir /tmp/living-creators-pilot \
  --retrieved-at 2026-08-06T15:00:00Z \
  --target-size 250
```

Validate any emitted observation file:

```bash
PYTHONPATH=. python3 -m sources.media.pilot validate \
  /tmp/living-creators-pilot/observations.ndjson
```

Build a deterministic cohort from source-native seeds:

```bash
PYTHONPATH=. python3 -m sources.media.pilot cohort \
  --seeds tests/sources_creators_media/fixtures/seeds.ndjson \
  --target-size 250 \
  --generated-at 2026-08-06T15:00:00Z \
  --out /tmp/cohort-manifest.json
```

Export the machine-readable source policy registry:

```bash
PYTHONPATH=. python3 -m sources.media.pilot policies \
  --out /tmp/source-policies.json
```

Run tests:

```bash
PYTHONPATH=. python3 -m unittest discover \
  -s tests/sources_creators_media -v
```

## Fixture results

The checked-in fixture run is intentionally small and public-safe:

- 16 valid observations across 9 source adapters;
- 26 source-native observed entities;
- 12 Work/Event/Venue observations and 15 contribution edges;
- 4 identity review candidates: 1 shared authority-ID candidate and 3 explicit-link candidates;
- 0 automatic identity acceptances;
- 4 fixture-labelled reviews, with 2 accepted and 2 true positives, yielding fixture precision 1.0; this is **not** a production precision estimate;
- complete source-policy/removal coverage for all 9 fixture sources;
- no transcript, audio, video, article body, abstract, or full-text payload retained.

The fixture cohort targets 250 but contains only 10 source-native seed rows (5 GitHub seeds and 5 modern-author seeds). The production command and contract are ready, but a current People Graph seed export and current modern-author snapshot were not available to this isolated lane. The manifest therefore reports `fixture_only`, `actual_size: 10`, and 240 unfilled slots rather than fabricating people.

See `pilot-metrics.fixture.json`, `cohort-manifest.fixture.json`, `bridge-candidates.fixture.json`, and `source-policies.json` for exact machine-readable results.

## Recommended next source

Start with publisher RSS feeds that expose Podcasting 2.0 `podcast:person` rows. They are the lowest-cost bridge source in this lane: the publisher controls the feed, roles and explicit profile URLs can be literal evidence, updates can use normal HTTP cache validators, and no API credential is required. Use Podcast Index only to discover feeds and reconcile source-native podcast IDs within its current cache/retention boundary.
