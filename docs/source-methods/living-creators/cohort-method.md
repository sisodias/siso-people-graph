# Reproducible cohort method

## Target

The intended production cohort is approximately 250 high-overlap people, balanced initially between current GitHub creators/maintainers and modern technical authors. Members remain source-native seeds; the manifest never assigns a canonical People Graph ID.

## Required seed fields

Each NDJSON seed must include:

- `seed_version: living-creator-seed-0.1`;
- a unique seed ID, source ID, and source-native ID;
- a display label for review only;
- one or more domains;
- at least one stable source-native identifier that is not a name, company, location, biography, topic, or handle;
- explicit links, if any;
- living evidence state: `living`, `likely_living`, or `unknown`, with a receipt.

The selector rejects name-only seeds, deduplicates by seed ID, orders deterministically by source and content digest, fills requested source targets, and then fills remaining slots round-robin.

## Fixture versus production

The checked-in fixture has 10 seeds: five GitHub and five modern-author examples. It intentionally asks for a target of 250 so the manifest proves the underfill behavior. The result is:

```json
{
  "target_size": 250,
  "actual_size": 10,
  "status": "fixture_only",
  "unfilled_slots": 240
}
```

No production People Graph database, current source export, or network credential is committed or assumed. A later run should supply a current source-native export and include snapshot receipts/digests in the manifest. Re-running with the same seed rows and timestamp yields byte-stable JSON ordering.
