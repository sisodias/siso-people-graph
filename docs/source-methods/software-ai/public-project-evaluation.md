# Public-project evaluation before implementation

Reviewed 2026-08-06. This lane deliberately implements only a small, offline
normalization contract. It does not duplicate full API clients or an entity
resolution engine.

| Project | License/data terms observed | Relevant capability | Decision for this pilot |
| --- | --- | --- | --- |
| `github/rest-api-description` | MIT | Machine-readable GitHub REST schema. | **Reference/adopt later.** A production network collector should generate request/response models from the official OpenAPI description rather than hand-maintain broad endpoint schemas. The fixture adapter remains dependency-free. |
| `PyGithub/PyGithub` | LGPL-3.0/GPL-3.0 licenses reported by GitHub | Mature typed Python GitHub REST client. | **Do not vendor.** It is more client surface than this offline pilot needs. Reconsider as an optional production dependency only after license and operational review. |
| `ecosyste-ms/packages` and `ecosyste-ms/repos` | AGPL-3.0 code; API data stated CC BY-SA 4.0 | Cross-ecosystem package/repository normalization. | **Consume data/API, do not copy service code.** Keep attribution, source IDs, and share-alike implications visible. This is the preferred npm first pass. |
| `huggingface/huggingface_hub` | Apache-2.0 | Official API client for models, datasets, Spaces, revisions, and cards. | **Recommended for production acquisition.** The current fixture adapter mirrors only the common envelope and keeps tests offline. |
| `pypi/warehouse` | Apache-2.0 | Canonical PyPI service implementation and API semantics. | **Reference, do not embed.** Use documented Index/JSON APIs and HTTP caching rather than service internals. |
| `SoftwareHeritage/swh-model` / `swh.model` | GPL-3.0 | Canonical SWH object model and SWHID handling. | **Reference concepts; no vendoring.** Production can use official SWHID tooling after license review, but the pilot stores literal SWHIDs only. |
| `package-url/purl-spec` | MIT for purl-spec software; ECMA-427 standard has separate terms | Standard package coordinate syntax. | **Adopt the standard.** The pilot implements only bounded PyPI/Cargo/npm formatting; production should use `packageurl-python` or equivalent conformance tests. |
| `moj-analytical-services/splink` | MIT | Probabilistic record linkage at scale. | **Evaluated and intentionally deferred.** This lane lacks sufficient independent identity fields and must not convert display names/logins into canonical people. It emits evidence receipts for a separate identity lane. |
| `dedupeio/dedupe` | MIT | Supervised/fuzzy entity resolution. | **Evaluated and intentionally deferred.** Human-labeled match/non-match sets and an explicit merge/reversal policy would be required before use. |

## Why no identity resolver is shipped here

The available software/package/Hub observations mostly contain mutable handles,
repository paths, free-text names, and project URLs. That is useful evidence but
not enough to justify a canonical person merge. The pilot therefore:

- preserves source-native account/organisation records;
- records literal cross-platform identifiers only when a receipt points to a
  stable source ID;
- rejects name/company/location/bio identifier schemes;
- exposes conflicts and temporal changes to the future identity lane;
- never writes a canonical ID, merge target, or universal score.

This is not an anti-linkage decision. It is a sequencing decision: acquire
replayable evidence first, then train/evaluate identity resolution against
reviewed ground truth in the lane that owns identity policy.
