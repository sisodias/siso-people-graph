# Source method cards: software, packages, and AI creators

**Review date:** 2026-08-06  
**Pilot mode:** offline, synthetic, replayable fixtures  
**Rights posture:** metadata only; no private repository content, gated model
payloads, package archives, email enrichment, or production personal-data dump.
Terms and policies can change, so a production collector must record the exact
terms revision and retrieval receipt for every snapshot.

## Identifier policy used by every card

An identifier is accepted only when the source exposes a literal value and the
adapter can state its scope, stability, uniqueness, and evidence. Names,
display names, companies, locations, bios, and textual author strings are not
identifiers. A login or repository path can be useful, but is explicitly marked
mutable. Cross-platform matches are evidence receipts, not merges.

## GitHub REST / GraphQL

| Field | Pilot decision |
| --- | --- |
| Purpose | Accounts, organisations, repositories, releases, current state, and selected contribution edges. |
| Stable identifiers | Numeric `account.id`, numeric `repository.id`, release ID, and GraphQL node IDs, all source scoped. |
| Mutable identifiers | Login and `owner/name` repository full name. Rename/transfer observations retain the stable numeric ID. |
| Acquisition | Start from a bounded cohort manifest. Use conditional requests and batched GraphQL only for fields absent from snapshots. |
| Cost | High at broad scale because current-state enrichment is API-call limited. |
| Rights | Public metadata under the GitHub Terms of Service effective 2026-04-27 in this review. Do not use the API to spam, profile private behavior, or retain removed personal data without a lawful purpose. |
| Deletion/update | Re-fetch by numeric ID; preserve the prior observation and append a tombstone/state observation when the source returns removal or access loss. |
| Promote when | Numeric-ID continuity survives rename/transfer fixtures and production receipts include API version, ETag/Last-Modified, and terms revision. |
| Kill when | Collection requires broad search by mutable login, private data, or inferred real-name resolution. |

Official references:

- https://docs.github.com/en/rest/users/users#get-a-user-using-their-id
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service

## GH Archive

| Field | Pilot decision |
| --- | --- |
| Purpose | Public GitHub event chronology without repeatedly polling current-state APIs. |
| Identifier | Literal event ID, actor numeric ID, repository numeric ID, and event timestamp. |
| Acquisition | Hourly archives or bounded BigQuery windows; retain archive hour plus event ID as locator. |
| Cost | Low for time-bounded temporal evidence; expensive if replaying all history indiscriminately. |
| Rights | Public event metadata remains subject to GitHub terms and source deletion/visibility changes. |
| Deletion/update | Treat archives as historical observations, not proof of current availability. Suppress from current views when the live source is deleted or restricted. |
| Promote when | Event types and payload summaries are limited to a documented allowlist. |
| Kill when | The use case needs private events, complete audit guarantees, or identity resolution from actor names. |

Reference: https://www.gharchive.org/

## ecosyste.ms Packages / Repos

| Field | Pilot decision |
| --- | --- |
| Purpose | Normalized cross-registry package, dependency, maintainer, and repository metadata; first-pass npm coverage. |
| Identifier | ecosyste.ms record ID plus source registry coordinate/PURL. Maintainers remain contribution edges. |
| Acquisition | API/export first, with local snapshot cache and source provenance retained. |
| Cost | Low to medium because one normalized source covers many registries. |
| Rights | ecosyste.ms project code is AGPL-3.0; API data is stated as CC BY-SA 4.0. Attribute the data and preserve source/revision information. |
| Deletion/update | Reconcile against source timestamps; do not treat normalized rows as more authoritative than the underlying registry. |
| Promote when | Coverage and freshness are measured against direct PyPI/crates/Hugging Face samples. |
| Kill when | A required registry/field is stale, missing provenance, or incompatible with downstream share-alike handling. |

Official references:

- https://ecosyste.ms/api
- https://github.com/ecosyste-ms/packages
- https://github.com/ecosyste-ms/repos

## PyPI

| Field | Pilot decision |
| --- | --- |
| Purpose | Python project/release metadata, hashes, `requires_dist`, project roles, and literal project URLs. |
| Identifier | Normalized project coordinate and PURL for the Work; versioned PURL and artifact SHA-256 for releases. PyPI usernames are source-scoped and stability is unknown. |
| Acquisition | Use Index API serials for change detection; fetch JSON only for the selected cohort and cache with ETags. |
| Cost | Medium if every project needs JSON; low for index-level change detection. |
| Rights | Public metadata under PyPI Terms of Service effective 2025-03-27 in this review. Distribution files retain their own licenses; this pilot does not download them. |
| Deletion/update | Respect project deletion/transfer, preserve prior observations, and do not assume a reused project name denotes the same maintainer. |
| Promote when | Owner-role acquisition is reproducible and version/file hashes are complete for the cohort. |
| Kill when | Ownership would be inferred from free-text author/maintainer fields or download counts are treated as a person score. |

Official references:

- https://docs.pypi.org/api/json/
- https://docs.pypi.org/api/index-api/
- https://policies.python.org/pypi.org/Terms-of-Service/

## crates.io / Cargo index

| Field | Pilot decision |
| --- | --- |
| Purpose | Crate coordinates, immutable version rows except yank state, checksums, dependencies, and selected owner edges. |
| Identifier | Cargo PURL for package/version; artifact SHA-256; crates.io owner ID where present. |
| Acquisition | Read versions/checksums/dependencies from the Git or sparse index. Reserve API lookups for bounded owner metadata. |
| Cost | Low for index data; medium for owner enrichment. |
| Rights | Public registry metadata; record policy/docs retrieval date and preserve package-level license expressions. Do not mirror `.crate` contents in this lane. |
| Deletion/update | Version rows are append-oriented, but yank state can change. Emit a new observation rather than overwriting history. |
| Promote when | Index commit/ETag and owner-lookup receipts are captured. |
| Kill when | A collector repeatedly scans the sparse endpoint instead of using incremental index/cache semantics. |

Official reference: https://doc.rust-lang.org/cargo/reference/registry-index.html

## Software Heritage

| Field | Pilot decision |
| --- | --- |
| Purpose | Verify that known repositories/releases have archived source objects and retain intrinsic archive identifiers. |
| Identifier | SWHID for snapshot, revision, release, directory, or content; global, stable, unique by object content/structure. |
| Acquisition | Point lookup for already-known origins/SWHIDs. Store metadata and locator only. |
| Cost | Low for verification, high and inappropriate for bulk discovery through the public API. |
| Rights | Archive metadata only in this lane. Archived code keeps original licensing; API/personal-data restrictions still apply. |
| Deletion/update | SWHIDs are intrinsic; origin visit status and availability are separate time-varying observations. |
| Promote when | Repository/release records already carry source IDs or origin URLs that can be verified cheaply. |
| Kill when | The proposal depends on bulk API extraction or treats archival presence as permission to redistribute code. |

Official references:

- https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html
- https://archive.softwareheritage.org/api/
- https://archive.softwareheritage.org/terms/

## Hugging Face Hub

| Field | Pilot decision |
| --- | --- |
| Purpose | Public account/organisation, model, dataset, Space, revision, card license, and model–dataset–Space relationship metadata. |
| Stable identifiers | Git commit SHA for a revision. |
| Mutable identifiers | Hub namespace/repository path and account handle. The adapter does not pretend a path is an immutable creator ID. |
| Acquisition | Paginated public API metadata first; fetch cards only for selected public, non-gated cohort records. |
| Cost | Medium; pagination and card retrieval can be bounded independently. |
| Rights | Public metadata under Hugging Face Terms of Service effective 2022-09-15 in this review. Model/dataset/Space content has item-specific licenses; gated/private payloads are excluded. |
| Deletion/update | Preserve revision observations, but remove/suppress current availability when a repo is deleted, gated, or made private. |
| Promote when | Model, dataset, and Space types stay distinct and all metrics are timestamped. |
| Kill when | The collector downloads weights/datasets by default or infers a person from namespace similarity. |

Official references:

- https://huggingface.co/docs/hub/repositories
- https://huggingface.co/docs/hub/api
- https://huggingface.co/terms-of-service

## Direct npm registry access — deferred

The pilot represents npm through ecosyste.ms. A direct npm adapter is not yet
justified because the normalized layer already supplies the required bounded
fields for this cohort. Add direct npm deltas only after measuring missing
ownership, version, dependency, and freshness fields and completing a separate
terms/rate-limit review.

## Recommended production-scale subset

1. **ecosyste.ms Packages/Repos** for broad package/dependency discovery,
   including npm, with source attribution.
2. **GitHub numeric-ID enrichment** only for repositories/accounts already in the
   cohort, plus a bounded GH Archive window for temporal events.
3. **Hugging Face public metadata** for models, datasets, Spaces, and revision
   heads; no payload download by default.
4. **PyPI Index and Cargo index deltas** to validate registry-native release,
   checksum, dependency, and owner details.
5. **Software Heritage point verification** only for known repositories/releases.

This order maximizes evidence coverage per network request while preserving a
clear path back to the authoritative source.
