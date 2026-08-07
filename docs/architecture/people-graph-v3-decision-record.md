# Decision record — People Graph v3 ontology

**Status:** architecture decisions for `3.0.0-draft.1`  
**Base:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Source register:** [`people-graph-v3-evidence-ledger.md`](people-graph-v3-evidence-ledger.md)

This file records reviewable rationale, alternatives, consequences, confidence, and reversal triggers. It is the shareable reasoning record. It intentionally does not reproduce private token-by-token model deliberation; agents need evidence and decision logic, not inaccessible internal scratch text.

## PGV3-D001 — Additive rebuild beside v2

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-003, SRC-004
- **Decision:** Build a fresh, standalone v3 database from declared snapshots and envelopes; never alter the current v2 asset in this PR.
- **Alternatives rejected or deferred:** In-place ALTER migration; destructive replacement; waiting for another lane.
- **Consequences:** Preserves current behavior and source reconstruction. Requires explicit future consumer cutover.
- **Reversal/next-review trigger:** Reconsider only after source manifests, parity checks, and a rollback-tested release process exist.
- **Confidence:** `high`
- **Executable coverage:** `test_schema_and_sample_apply_with_foreign_keys_clean`

## PGV3-D002 — Layer source observations separately from canonical entities

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-003, SRC-004, SRC-008
- **Decision:** Store immutable source-native observations and envelope receipts before any canonical entity exists.
- **Alternatives rejected or deferred:** Insert source records directly into canonical person rows; treat envelope subject IDs as canonical IDs.
- **Consequences:** Prevents import-time identity assertions and preserves source disagreement. Adds an explicit resolution step.
- **Reversal/next-review trigger:** Reconsider only if a source contract itself is the accepted canonical authority for a bounded entity class.
- **Confidence:** `high`
- **Executable coverage:** `test_envelope_import_cannot_assign_a_canonical_id; test_source_observations_and_identity_decisions_are_append_only`

## PGV3-D003 — Use opaque canonical entity IDs

- **Status:** `accepted`
- **Evidence:** SRC-003, SRC-005, SRC-007
- **Decision:** Generate canonical IDs outside the DDL; never derive them from names, handles, or source-native IDs.
- **Alternatives rejected or deferred:** Namespaced source IDs; normalized-name keys; mutable login IDs.
- **Consequences:** Names and handles may change without rewriting identity. Mapping now requires explicit evidence.
- **Reversal/next-review trigger:** Reconsider only for an entity class governed by one immutable external authority and a documented migration policy.
- **Confidence:** `high`
- **Executable coverage:** `test_unicode_and_alias_search_preserve_non_latin_text`

## PGV3-D004 — Register identifier semantics before identity use

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-003, SRC-005
- **Decision:** Each scheme declares scope, uniqueness, mutability, trust class, authority, normalization version, and auto-resolution eligibility.
- **Alternatives rejected or deferred:** One untyped external_ids table; hard-coded confidence per matching method.
- **Consequences:** Strong identifiers can be constrained while mutable/non-unique values may collide safely.
- **Reversal/next-review trigger:** Scheme definitions require governance and versioning as sources change.
- **Confidence:** `high`
- **Executable coverage:** `test_unique_identifiers_are_enforced_within_scope; test_conflicting_stable_ids_block_identity_acceptance`

## PGV3-D005 — Treat handles and names as aliases, not global IDs

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-005, SRC-007
- **Decision:** Store time-bounded Unicode aliases; stable platform-issued numeric IDs may be identifiers under a registered scheme.
- **Alternatives rejected or deferred:** ASCII-normalized canonical name keys; login-derived person IDs.
- **Consequences:** Supports rename history and non-Latin names without accidental merges.
- **Reversal/next-review trigger:** Locale-specific collation/transliteration remains a query concern, not identity truth.
- **Confidence:** `high`
- **Executable coverage:** `test_unicode_and_alias_search_preserve_non_latin_text; test_unique_identifiers_are_enforced_within_scope`

## PGV3-D006 — Make Works first-class

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-003, SRC-007, SRC-008
- **Decision:** Model Work, version, venue, contribution role/order/time, citation, dependency, and locator independently.
- **Alternatives rejected or deferred:** Keep title/content_ref only on person_content edges; one generic polymorphic edge table.
- **Consequences:** Supports source-native Works and later canonicalization without losing roles or editions.
- **Reversal/next-review trigger:** The unified Work-version subtype is provisional and may split after real pilots.
- **Confidence:** `high`
- **Executable coverage:** `test_work_subtypes_roles_versions_citations_and_dependencies`

## PGV3-D007 — Separate evidence from assertions and relationships

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-010, SRC-011
- **Decision:** Evidence records carry locator, observation time, extraction/model lineage, and policy; assertions and temporal relationships reference evidence and review state.
- **Alternatives rejected or deferred:** Store free-text biography/topic fields as accepted person facts; one generic edge with no epistemic type.
- **Consequences:** A source record, accepted claim, derived relation, and model hypothesis remain distinguishable.
- **Reversal/next-review trigger:** Predicate governance and review workflows remain implementation seams.
- **Confidence:** `high`
- **Executable coverage:** `test_model_output_is_explicit_and_not_source_evidence`

## PGV3-D008 — Make identity decisions append-only and merges reversible

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-002, SRC-003, SRC-005
- **Decision:** Record candidate method/version, positive/negative/conflicting evidence, append-only decisions, clusters, temporal memberships, and redirects.
- **Alternatives rejected or deferred:** Delete losing rows; mutate one merge pointer without decision history; treat accepted claim status as sufficient canonicalization.
- **Consequences:** Undo closes derived intervals and reactivates entities while source observations survive.
- **Reversal/next-review trigger:** Candidate generation and canonical selection policy are deliberately outside this DDL.
- **Confidence:** `high`
- **Executable coverage:** `test_conflicting_stable_ids_block_identity_acceptance; test_identity_merge_can_be_reversed_without_losing_sources`

## PGV3-D009 — Block acceptance while recorded identity conflicts are open

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-005
- **Decision:** A database trigger rejects an accepted identity decision when an open conflict row exists.
- **Alternatives rejected or deferred:** Trust a scalar confidence alone; record conflict only in prose.
- **Consequences:** Makes contradictory stable IDs a hard, visible gate.
- **Reversal/next-review trigger:** The identity lane must actually detect and insert conflicts; the DDL cannot discover them itself.
- **Confidence:** `high`
- **Executable coverage:** `test_conflicting_stable_ids_block_identity_acceptance`

## PGV3-D010 — Carry rights, privacy, publication, terms, and deletion state

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-009, SRC-010
- **Decision:** Policy state is referenced at source snapshot, observation, Work/version, evidence, assertion, and projection boundaries; status events preserve tombstones/removal receipts.
- **Alternatives rejected or deferred:** Assume public visibility permits retention/reuse; keep one repository-level license note.
- **Consequences:** Allows public-safe projections and source-specific removal handling.
- **Reversal/next-review trigger:** Production policy enforcement and raw-payload deletion mechanisms remain external services.
- **Confidence:** `high`
- **Executable coverage:** `test_rights_privacy_and_publication_coverage`

## PGV3-D011 — Keep vocabularies namespaced and crosswalk explicitly

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-002
- **Decision:** Terms retain vocabulary namespace/version; crosswalks carry mapping type, confidence, evidence, method version, and review status.
- **Alternatives rejected or deferred:** Flatten labels into one topic string namespace.
- **Consequences:** Prevents false equivalence across GitHub topics, LCSH, curated terms, and future sources.
- **Reversal/next-review trigger:** Crosswalk governance and transitive reasoning are not defined here.
- **Confidence:** `high`
- **Executable coverage:** `test_vocabularies_remain_namespaced_and_crosswalks_explicit`

## PGV3-D012 — Use Unicode FTS for canonical labels and accepted aliases

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-003, SRC-005, SRC-007
- **Decision:** Maintain one FTS row per canonical label/accepted alias using unicode61 and diacritic removal for Latin lookup.
- **Alternatives rejected or deferred:** ASCII-only normalized names; LIKE scans only.
- **Consequences:** Preserves non-Latin text and supports accent-insensitive Latin search.
- **Reversal/next-review trigger:** Not full locale-aware collation, morphology, or transliteration.
- **Confidence:** `medium`
- **Executable coverage:** `test_unicode_and_alias_search_preserve_non_latin_text`

## PGV3-D013 — Replace universal score/tier with named projections

- **Status:** `accepted`
- **Evidence:** SRC-001, SRC-002, SRC-003, SRC-004, SRC-008
- **Decision:** Projection definitions and runs record method/version, scope, as-of time, parameters, input digest, uncertainty, rights, and publication state.
- **Alternatives rejected or deferred:** Copy rank_score/primary_tier into v3 canonical person fields.
- **Consequences:** Different metrics can coexist without claiming one timeless person ranking.
- **Reversal/next-review trigger:** Projection computation and method cards belong to reasoning/build lanes.
- **Confidence:** `high`
- **Executable coverage:** `test_projections_are_named_versioned_scoped_and_uncertain`

## PGV3-D014 — Store exact pg-observation-0.1 receipts

- **Status:** `accepted`
- **Evidence:** SRC-001
- **Decision:** Persist the exact JSON receipt with shape checks and a digest; map children to source-observation tables and stop before canonicalization.
- **Alternatives rejected or deferred:** Change the shared envelope in this lane; import only selected fields without replay receipt.
- **Consequences:** Enables replay and cross-lane compatibility while respecting independent source adapters.
- **Reversal/next-review trigger:** Canonical JSON byte serialization and digest verification are importer responsibilities.
- **Confidence:** `high`
- **Executable coverage:** `test_envelope_import_cannot_assign_a_canonical_id`

## PGV3-D015 — Keep one logical schema; defer physical sharding

- **Status:** `deferred_physical_choice`
- **Evidence:** SRC-001, SRC-009
- **Decision:** Define one logical contract that may later place high-volume observations in attached SQLite shards or an external columnar data plane.
- **Alternatives rejected or deferred:** Prematurely prescribe one giant SQLite file; prescribe a distributed database before measurement.
- **Consequences:** Independent lanes can target stable semantics while build benchmarks select physical layout later.
- **Reversal/next-review trigger:** Requires 10× observation load benchmarks, query traces, and operational constraints.
- **Confidence:** `medium`
- **Executable coverage:** `not yet benchmarked`

## PGV3-D016 — Use direct observation provenance for canonical labels in draft.1

- **Status:** `provisional`
- **Evidence:** SRC-001, SRC-010
- **Decision:** entity.label_observation_id points to one source observation for the draft fixture.
- **Alternatives rejected or deferred:** Require a multi-evidence accepted label assertion from day one; store an unproven label with no source.
- **Consequences:** Keeps the draft executable and traceable with a narrow field.
- **Reversal/next-review trigger:** May evolve to accepted multi-evidence label assertions after identity/query pilots.
- **Confidence:** `medium`
- **Executable coverage:** `foreign-key coverage only`

## PGV3-D017 — Use one work_version table in draft.1

- **Status:** `provisional`
- **Evidence:** SRC-001, SRC-003, SRC-007
- **Decision:** Represent expression, edition, release, revision, translation, and manifestation through a constrained version_type.
- **Alternatives rejected or deferred:** Separate FRBR-like subtype tables immediately; collapse all versions into Work.
- **Consequences:** Provides first-class version semantics with low fixture complexity.
- **Reversal/next-review trigger:** Split when real Book/software/media pilots demonstrate subtype-specific invariants.
- **Confidence:** `medium`
- **Executable coverage:** `test_work_subtypes_roles_versions_citations_and_dependencies`

## PGV3-D018 — Do not encode automatic identity acceptance thresholds

- **Status:** `deferred_policy`
- **Evidence:** SRC-001, SRC-005
- **Decision:** The schema records eligibility and evidence but leaves thresholds and automatic acceptance to a versioned identity policy.
- **Alternatives rejected or deferred:** Hard-code 0.98 or another confidence as globally safe in DDL.
- **Consequences:** Prevents one source/method calibration from becoming ontology.
- **Reversal/next-review trigger:** Identity lane must publish precision measurements and conflict policy.
- **Confidence:** `high`
- **Executable coverage:** `schema permits policy; no precision benchmark in this lane`
