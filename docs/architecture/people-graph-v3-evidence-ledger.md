# Evidence ledger — People Graph v3 ontology

**Status:** reconstructable source register for `3.0.0-draft.1`  
**Base audited:** `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Method:** separate observations, inferences, decisions, and unresolved questions.

## Epistemic labels

- **Observed:** directly visible in a pinned source file, prompt, test result, or Git object.
- **Inference:** a bounded conclusion derived from one or more observations; it is not a source fact.
- **Decision:** the design choice adopted by this lane, with alternatives and consequences recorded separately.
- **Unresolved:** deliberately deferred because the available evidence does not select one safe answer.

## Pinned source register

| ID | Class | Repository / ref | Path / blob | Role and limits |
| --- | --- | --- | --- | --- |
| SRC-001 | `primary_requirement` | `user-supplied source@077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d` | `Pasted text.txt / shared preamble + Prompt 3` | **Observed:** Defines branch, owned paths, additive/no-wait posture, exact model requirements, invariants, deliverables, offline tests, and the pg-observation-0.1 boundary.<br>**Used for:** Acceptance contract and scope control.<br>**Limit:** The complete source contains other lanes; their implementation choices are not authority for this lane. |
| SRC-002 | `primary_current_state` | `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98` | [`README.md`](https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/README.md)<br>blob `3ae7738eed163cabb72ed5ea4d57d38453ec40f1` | **Observed:** States the graph purpose and measured inventory; keeps roles on edges; describes identity claims and reversible merges; rejects duplicated derived tier/score state; reports only three current cross-domain stitches.<br>**Used for:** Preserved successful v2 principles and explicit current limitations.<br>**Limit:** README claims describe the release; they are not a complete executable specification. |
| SRC-003 | `primary_current_state` | `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98` | [`schema/people_schema_v2.sql`](https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/schema/people_schema_v2.sql)<br>blob `07b70a2eaf8db48d741010d2d5f31810a0c9d0d1` | **Observed:** Canonical person IDs are source-shaped; external identifier semantics are not registered; Works remain content_ref/title strings on person edges; identity claims have coarse status; score/tier columns coexist; contemporaries impute death as birth+80.<br>**Used for:** V2 compatibility table and separation of observation, entity, Work, identity, assertion, relationship, and projection layers.<br>**Limit:** Schema comments include design intent; behavior also depends on loaders and consumers. |
| SRC-004 | `primary_current_state` | `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98` | [`loaders/build_people_graph_v2.py`](https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/loaders/build_people_graph_v2.py)<br>blob `7983db530d242b386fcd3c8277718010b7a43034` | **Observed:** Prefers source reconstruction over in-place migration, but maps book records to existing people by normalized name and carries source-specific rank values into one column.<br>**Used for:** Rebuild strategy, no-silent-name-merge invariant, and named projection design.<br>**Limit:** This lane did not modify or execute a production build. |
| SRC-005 | `primary_current_state` | `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98` | [`loaders/match_identities.py`](https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/loaders/match_identities.py)<br>blob `541c68e7083e54327141aaed37f004579b024c4c` | **Observed:** Comparison normalization removes non-ASCII characters; every external_ids platform/value pair is treated as the strongest shared-ID signal; candidate rows do not themselves create canonical clusters or redirects.<br>**Used for:** Unicode-preserving aliases, identifier scheme registry, explicit conflicts/decisions, and reversible clusters.<br>**Limit:** Candidate prevalence and production precision were not measured in this lane. |
| SRC-006 | `primary_current_state` | `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98` | [`loaders/ask.py`](https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/loaders/ask.py)<br>blob `37e19c92d242bc979eb2ab55b4f6f6a02872083d` | **Observed:** Read-only query intent is explicit, but topology is hard-coded, missing domains are skipped, and one result is selected by content count rather than an accepted canonical decision.<br>**Used for:** Capability-detecting coexistence seam and provenance/status requirements for future query surfaces.<br>**Limit:** Query implementation belongs to another lane and is unchanged here. |
| SRC-007 | `cross_repository_current_state` | `sisodias/siso-book-library@be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b` | [`scripts/build_people_graph.py`](https://github.com/sisodias/siso-book-library/blob/be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b/scripts/build_people_graph.py)<br>blob `08b667b448c3acbc4bc0357f378270d46892e071` | **Observed:** Preserves contributor roles and raw variants, but constructs identity keys from normalized names/life years and removes non-ASCII characters from the key.<br>**Used for:** Observation-first import seam, source-native contributor roles, Unicode preservation, and opaque canonical IDs.<br>**Limit:** Book source metadata cannot independently prove canonical cross-domain identity. |
| SRC-008 | `cross_repository_current_state` | `sisodias/siso-book-library@be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b` | [`scripts/load_into_people_graph.py`](https://github.com/sisodias/siso-book-library/blob/be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b/scripts/load_into_people_graph.py)<br>blob `de4e9fd91c076fd514887c82bd334dde43271d7b` | **Observed:** Matches book people to canonical rows by normalized name, embeds Gutenberg IDs as content references, filters contribution roles for the legacy edge, and stores work count as rank_score.<br>**Used for:** First-class Work/contribution model and prohibition on automatic canonicalization during envelope import.<br>**Limit:** Pinned historical cross-repository contract; a later Book lane may supersede it. |
| SRC-009 | `contextual_architecture` | `sisodias/great-library-of-siso@3c16cf0037384a5d6b24a785bde9a1a2554b07a9` | [`docs/siso-knowledge-model.html`](https://github.com/sisodias/great-library-of-siso/blob/3c16cf0037384a5d6b24a785bde9a1a2554b07a9/docs/siso-knowledge-model.html)<br>blob `dc1f74cdf77eea64f54f56c828ae996d8345a1e6` | **Observed:** Separates public registry identity, durable knowledge/index/graph responsibility, source discovery, evidence transformation, and external large-data custody.<br>**Used for:** Data-plane boundary, rebuildable projections, and rights/provenance posture.<br>**Limit:** Contextual system boundary only; not table-level authority for this SQLite draft. |
| SRC-010 | `contextual_architecture` | `sisodias/great-library-of-siso@3c16cf0037384a5d6b24a785bde9a1a2554b07a9` | [`docs/question-driven-research.html`](https://github.com/sisodias/great-library-of-siso/blob/3c16cf0037384a5d6b24a785bde9a1a2554b07a9/docs/question-driven-research.html)<br>blob `2ec1c5f688fa25402d4cab71cd46f8500e8b4adb` | **Observed:** Separates source cards from claims, requires claim receipts/scope/confidence, makes decisions carry evidence and reversal triggers, and treats derived answers as versioned releases.<br>**Used for:** Evidence/assertion lineage, decision records, and explicit uncertainty/review state.<br>**Limit:** Contextual research method; schema details remain a People Graph decision. |
| SRC-011 | `contextual_architecture` | `sisodias/great-library-of-siso@3c16cf0037384a5d6b24a785bde9a1a2554b07a9` | [`registry/works/frontier-question-gq-009.json`](https://github.com/sisodias/great-library-of-siso/blob/3c16cf0037384a5d6b24a785bde9a1a2554b07a9/registry/works/frontier-question-gq-009.json) | **Observed:** Records the registry/Foundry/Knowledge/Evidence-Engine boundaries and states that question-driven evidence selection is necessary rather than extracting everything.<br>**Used for:** Confirmation that breadth alone is not the objective and that evidence-bearing outputs need explicit lineage.<br>**Limit:** Context only; the full record was not treated as a source of production People Graph facts. |

## Observation → inference → decision trace

| Trace | Observed evidence | Bounded inference | Adopted decision |
| --- | --- | --- | --- |
| T-001 | `SRC-003`, `SRC-004`, and `SRC-008` show source-shaped IDs and name-based cross-source collapse. | A display name cannot safely serve as the canonical identity boundary at larger scale. | Opaque canonical entity IDs; observation import never creates a canonical ID; identity is a separate reviewed decision. |
| T-002 | `SRC-005` groups all external-ID schemes together and strips non-ASCII characters during comparison. | Identifier strength is scheme-specific, while names and handles are mutable/non-unique. | Register scope, uniqueness, mutability, trust, normalization version, and auto-resolution eligibility before canonical assignment. Preserve Unicode labels and aliases. |
| T-003 | `SRC-003` and `SRC-008` represent Works through `content_ref`/title strings and source-specific edge payloads. | Work versions, contributor order, citations, dependencies, and locators cannot be governed as strings on a person edge. | First-class Work, Work-version, contribution, venue, citation, dependency, and locator tables. |
| T-004 | `SRC-002` rejects duplicated derived state; `SRC-004` and `SRC-008` place incompatible source metrics in `rank_score`. | A universal person score loses method, scope, time, and uncertainty. | Named/versioned projection definitions, runs, source scopes, input digests, and uncertainty; no canonical rank column in v3. |
| T-005 | Prompt 3 requires every accepted fact to have provenance and observed time; `SRC-010` separates sources from claims and decisions. | Observation, evidence, claim, relationship, and decision are different epistemic objects. | Separate immutable observations, evidence, assertions, temporal relationships, and append-only identity decisions. |
| T-006 | Prompt 3 requires reversible corrections; v2 preserves losing rows but has no full candidate/conflict/decision/cluster lineage. | Reversal must close derived state without deleting source records. | Append-only decisions plus temporal memberships and redirects; tests prove undo leaves observations and both entities intact. |
| T-007 | Shared program rules require rights/terms/deletion semantics and prohibit raw production payloads in Git; `SRC-009` keeps large data outside Git. | Governance metadata must travel with each evidence-bearing layer. | Terms revision, rights, privacy, publication, digest, retention, deletion, and tombstone fields at source/snapshot/observation/Work/evidence/assertion/projection boundaries. |
| T-008 | `SRC-002` says source vocabularies are separate; Prompt 3 requires explicit crosswalks. | Equal labels do not imply equal concepts or authorities. | Namespaced/versioned vocabularies and evidence-backed term crosswalks. |
| T-009 | The source prompt requires a standalone parallel proposal that cannot wait for other lanes. | A schema that edits v2 or requires another PR would violate the coordination contract. | Additive `schema/v3/**`, synthetic fixtures, lane-local tests, and documented adapters; no v2 file edits. |

## Evidence not available in this lane

- No production v3 database, full source snapshot, bulk performance run, or release asset was built.
- No empirical precision threshold for automatic identity acceptance was established.
- No production rights review was performed for a real source pilot; fixtures are synthetic.
- No physical sharding benchmark selected one SQLite file, attached shards, or a columnar observation plane.
- No consumer cutover proved v2/v3 query parity.

These gaps are not silently filled. They remain explicit integration decisions and acceptance gates.
## Official SQLite implementation references


Reviewed on 2026-08-06 from the SQLite project documentation. These references
support implementation semantics, not People Graph domain claims:

- Foreign-key enablement and enforcement: <https://www.sqlite.org/foreignkeys.html>
- FTS5 and the `unicode61` tokenizer: <https://www.sqlite.org/fts5.html>
- JSON functions used by shape checks: <https://www.sqlite.org/json1.html>
- Partial unique indexes: <https://www.sqlite.org/partialindex.html>
- Trigger behavior and cautions: <https://www.sqlite.org/lang_createtrigger.html>
- Transaction boundaries: <https://www.sqlite.org/lang_transaction.html>

The executable suite remains the acceptance evidence for this exact DDL/runtime;
the documentation explains the underlying SQLite contract.
