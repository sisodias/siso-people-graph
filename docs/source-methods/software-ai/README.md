# Software and AI creator observation pilot

This lane tests whether public software/package/AI metadata can produce useful,
replayable People Graph observations **without** creating canonical identities,
silent name merges, or a cross-domain popularity score.

## Run the pilot

From the repository root:

```bash
PYTHONPATH=. python -m unittest discover -s tests/sources_software_ai -v

PYTHONPATH=. python -m sources.software.pilot export \
  --fixtures tests/sources_software_ai/fixtures \
  --out /tmp/software-ai.ndjson \
  --metrics-out /tmp/software-ai-metrics.json

PYTHONPATH=. python -m sources.software.pilot validate /tmp/software-ai.ndjson
```

The export is deterministic. The committed fixture manifest fingerprints the
logical NDJSON output so later changes can be reviewed as data-contract changes,
not only code changes.

## What the pilot covers

- GitHub REST account, organisation, repository, release, rename, and transfer observations.
- GH Archive event-shaped temporal observations.
- PyPI package, release, owner/maintainer, checksum, dependency, and source-repository observations.
- crates.io package/index, owner, release, checksum, yank, and dependency observations.
- ecosyste.ms normalized npm/PyPI package, maintainer, repository, and dependency observations.
- Software Heritage snapshot/revision identifiers and origin links.
- Hugging Face Hub account, organisation, model, dataset, Space, revision, and model–dataset–Space links.

The fixtures are synthetic and deliberately adversarial: renamed users,
transferred repositories, organisation ownership, co-maintainers, an archived
repository, abandoned packages, a yanked release, and a source disagreement on
license metadata.

## Contract boundaries

Every output row is a `pg-observation-0.1` envelope with:

- source, snapshot, observed/retrieved timestamps, terms revision, rights state, and payload hash;
- a source-native subject and literal label;
- identifiers annotated with scope, stability, uniqueness, and evidence;
- contribution and relationship edges;
- a raw fixture pointer.

The validator rejects canonical-ID fields, merge targets, universal ranking
fields, and attempts to use names, companies, locations, biographies, or bios as
identifiers. Metrics such as stars, downloads, followers, likes, and runs remain
timestamped source observations.

## Files

- `method-cards.md` — source-by-source acquisition, identifier, rights, cost, and deletion notes.
- `public-project-evaluation.md` — reuse/license review of relevant public projects.
- `evidence-first-questions.md` — questions this evidence can answer that star rankings cannot.
- `pilot-metrics.md` and `pilot-metrics.json` — measured fixture-pilot results.
- `pilot-manifest.json` — fixture and deterministic-output fingerprints.
- `docs/handoffs/software-ai-pilot.md` — integration handoff for the ontology/core lane.
