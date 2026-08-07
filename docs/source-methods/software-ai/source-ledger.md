# Source ledger

**Reviewed for the pilot:** 2026-08-06  
**Rule:** official/primary documentation supports source facts; pilot design
choices are labelled as inferences or decisions. Terms and APIs can change, so a
production collector must record retrieval-time revisions and receipts.

## GitHub REST and GraphQL

**Official references**

- https://docs.github.com/en/rest/users/users#get-a-user-using-their-id
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
- https://github.com/github/rest-api-description

**Source facts used.** GitHub exposes numeric account and repository IDs, node
IDs, logins, repository full names, owners, contributors, releases, current
state, conditional-request mechanisms, and rate limits.

**Pilot interpretation.** Numeric IDs are source-scoped continuity evidence;
logins and repository paths are mutable. Neither proves a canonical human.
Broad enrichment is classified high-cost relative to indexes/snapshots, so the
recommended collector starts from a bounded cohort and uses conditional or
batched requests.

**Rights/update boundary.** Public metadata remains governed by current GitHub
terms. Production must not collect private behavior, must record API/terms
revision and caching receipts, and needs a suppression/tombstone path for
removal or access loss.

**Refresh triggers.** API version, identifier semantics, terms, rate limits,
GraphQL cost rules, or deletion behavior changes.

## GH Archive

**Reference**

- https://www.gharchive.org/

**Source facts used.** GH Archive publishes public GitHub event data in hourly
archives and documents BigQuery access.

**Pilot interpretation.** It is useful for bounded temporal evidence and literal
event/actor/repository IDs. Historical events do not prove current source
availability and must not be used to infer a person from a name.

**Refresh triggers.** Event payload/schema, coverage, delivery, access method,
or underlying GitHub policy changes.

## ecosyste.ms Packages and Repos

**Official references**

- https://ecosyste.ms/api
- https://github.com/ecosyste-ms/packages
- https://github.com/ecosyste-ms/repos

**Source facts used.** ecosyste.ms provides normalized package/repository APIs
and cross-ecosystem metadata. The project publishes code and data licensing
information on its official surfaces.

**Pilot interpretation.** It is the first-pass normalized discovery layer,
including npm, while registry-native sources remain available for validation.
Normalized observations never overwrite disagreements from PyPI/Cargo/Hugging
Face.

**Rights/update boundary.** Preserve attribution, source IDs, revisions, and
share-alike implications. A production system needs field-level freshness and
provenance checks.

**Refresh triggers.** License/data terms, API/export format, registry coverage,
freshness, provenance, or deletion semantics change.

## PyPI

**Official references**

- https://docs.pypi.org/api/json/
- https://docs.pypi.org/api/index-api/
- https://policies.python.org/pypi.org/Terms-of-Service/
- https://github.com/pypi/warehouse

**Source facts used.** PyPI exposes project/release metadata, files and hashes,
project URLs, dependency metadata, and index serials/change information.

**Pilot interpretation.** Project coordinates and PURLs identify package Works;
versioned PURLs and checksums identify releases/artifacts. Usernames are
source-scoped and free-text author/maintainer strings are not identity evidence.
Index/change APIs should drive deltas; selected project JSON should be cached.

**Rights/update boundary.** Distribution files have item-specific licenses and
are not downloaded. Production must handle project deletion, transfer, reuse,
and current terms.

**Refresh triggers.** API deprecations/fields, index serial semantics, project
role access, terms, transfer/deletion behavior, or package-name reuse policy.

## crates.io and Cargo index

**Official reference**

- https://doc.rust-lang.org/cargo/reference/registry-index.html

**Source facts used.** The registry index carries crate/version metadata,
checksums, dependencies, features, and yank state; owners may require bounded
API lookups.

**Pilot interpretation.** PURLs identify package/version Works, checksums identify
artifacts, and owners are contribution edges. Index deltas are preferred to
repeated broad endpoint scans.

**Rights/update boundary.** Do not mirror `.crate` payloads in this lane. Record
index revision/ETag and package license expressions. Yank state is time-varying.

**Refresh triggers.** Index schema/protocol, sparse-index behavior, owner API,
terms, or yank/deletion semantics change.

## Software Heritage

**Official references**

- https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html
- https://archive.softwareheritage.org/api/
- https://archive.softwareheritage.org/terms/

**Source facts used.** Software Heritage defines persistent intrinsic identifiers
for archived software objects and exposes archive APIs/origin information.

**Pilot interpretation.** SWHIDs are global stable object identifiers and are
valuable for point verification of already-known repositories/releases. The
public API is not treated as a bulk discovery channel.

**Rights/update boundary.** Archive metadata and identifiers do not grant
permission to redistribute archived code. Original licensing and current API/
personal-data terms still apply.

**Refresh triggers.** SWHID model/version, API terms, rate guidance, origin visit
semantics, or access/removal policy changes.

## Hugging Face Hub

**Official references**

- https://huggingface.co/docs/hub/repositories
- https://huggingface.co/docs/hub/api
- https://huggingface.co/terms-of-service
- https://github.com/huggingface/huggingface_hub

**Source facts used.** The Hub exposes public model, dataset, and Space metadata,
accounts/organisations, revisions, cards, licenses, and relationships; Git
revision hashes identify content history.

**Pilot interpretation.** Models, datasets, Spaces, and revisions remain distinct
Works. Namespace paths and handles are mutable. Public metadata can be collected
before selectively fetching cards; weights, datasets, gated, and private
payloads are excluded by default.

**Rights/update boundary.** Item/card/file licenses and access states can differ.
Production needs deletion/private/gated suppression and must not treat a namespace
as a canonical person.

**Refresh triggers.** API/card schema, repository typing, revision semantics,
terms, gated/private behavior, or license metadata changes.

## Package URL

**Official reference**

- https://github.com/package-url/purl-spec

**Source facts used.** Package URL defines a standard package-coordinate syntax.

**Pilot interpretation.** PURLs identify package/version Works, not maintainers.
The fixture adapter implements a bounded subset; production should use a
conformance-tested library or full spec tests.

**Refresh triggers.** PURL spec or ecosystem normalization rules change.

## Public projects evaluated for reuse

The branch records decisions for:

- GitHub REST OpenAPI description;
- PyGithub;
- ecosyste.ms packages/repos;
- `huggingface_hub`;
- PyPI Warehouse;
- Software Heritage model/SWHID tooling;
- Package URL tooling;
- Splink and Dedupe.

The acquisition pilot does not vendor these projects. Identity-resolution
libraries are deliberately deferred to the lane that owns reviewed ground truth,
automatic-acceptance policy, reversibility, and audit lineage.

## Source fact versus inference checklist

A production change is acceptable only when its review states:

1. the exact official source URL and retrieval date;
2. the literal source field or documented behavior relied upon;
3. the adapter inference, if any, separately from the source fact;
4. identifier scope/stability/uniqueness and counterexamples;
5. terms, rights, attribution, retention, deletion, and suppression obligations;
6. expected information gain, calls/bytes/time, and kill condition;
7. the fixture/test that makes the assumption falsifiable.
