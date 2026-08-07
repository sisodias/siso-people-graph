# Software/AI pilot metrics

**Measurement date:** 2026-08-06  
**Mode:** deterministic offline replay over synthetic fixtures  
**Network calls:** 0  
**Canonical merges:** 0  
**Universal scores:** 0

## Measured output

| Metric | Result |
| --- | ---: |
| Observation envelopes | 31 |
| Source adapters represented | 7 |
| Accounts | 4 |
| Organisations | 2 |
| Events | 2 |
| Works | 23 |
| Stable unique identifiers | 36 |
| Identifier observations | 98 |
| Contribution edges | 30 |
| Relationship edges | 35 |
| Timestamped metric observations | 43 |
| Literal cross-platform identity-evidence receipts | 8 |
| Temporal rename/transfer relationships | 2 |
| Archived works | 3 |
| Abandoned works | 3 |
| Deliberate source conflicts preserved | 1 |
| Rights/terms coverage | 31/31 (100%) |
| Declared-license coverage for Works | 21/23 (91.3%) |
| Fixture bytes | 21,710 |

The one conflict is intentional: the synthetic PyPI and ecosyste.ms observations
report different licenses for `pkg:pypi/vectorforge`. The metric is a test of
conflict preservation, not a claim about a real package.

## Work coverage

| Work type | Count |
| --- | ---: |
| Software repository | 3 |
| Software release | 2 |
| Software package | 6 |
| Software package release | 4 |
| Software Heritage snapshot/revision | 2 |
| AI model/dataset/Space | 3 |
| AI model/dataset/Space revisions | 3 |

## Adversarial cases represented

- GitHub login rename with a stable numeric account ID.
- Repository transfer from a user account to an organisation while preserving
  the numeric repository ID.
- Organisation ownership and publishing as a first-class entity type.
- Co-maintainers and contributors represented on edges, not as aliases.
- Cross-registry dependency edges using PURLs.
- Archived repository and abandoned package states.
- Yanked crate release.
- Software Heritage snapshot and revision identifiers.
- Hugging Face model–dataset–Space relationships plus revision SHAs.
- Contradictory source licenses preserved for review.

## Cost interpretation

The fixture pilot intentionally made no network calls, so it does not claim
throughput or API-call benchmarks. `pilot-metrics.json` records qualitative
source-cost profiles and the recommended acquisition order. The next online
pilot should measure requests, response bytes, cache-hit rate, retry/rate-limit
incidents, changed records per request, and source lag against a fixed cohort.

## Reproduce

```bash
PYTHONPATH=. python -m unittest discover -s tests/sources_software_ai -v

PYTHONPATH=. python -m sources.software.pilot export \
  --fixtures tests/sources_software_ai/fixtures \
  --out /tmp/software-ai.ndjson \
  --metrics-out /tmp/software-ai-metrics.json

sha256sum /tmp/software-ai.ndjson
```

Compare the digest with `pilot-manifest.json`. `pilot-metrics.json` is the
machine-readable source of truth for current counts.
