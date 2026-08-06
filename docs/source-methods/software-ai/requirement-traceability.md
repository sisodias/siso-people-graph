# Prompt 10 requirement traceability

Legend: **implemented** means executable code/fixtures/tests exist on the branch;
**documented** means the pilot records a decision or method but deliberately does
not make a production claim; **deferred** means a measured/rights/policy gate is
recorded.

| Prompt requirement | Artifact(s) | Verification | Status |
| --- | --- | --- | --- |
| Work from current main and use shared envelope | branch base; `sources/software/envelope.py` | envelope version test and manifest | implemented |
| Stay inside exclusive paths | PR changed-file list; handoff | complete PR diff inspection | implemented |
| Never assign canonical IDs | envelope forbidden-key validator | `test_rejects_canonical_or_rank_fields`; serialized record assertions | implemented |
| Accounts and organisations | GitHub/Hugging Face adapters and fixtures | `test_organisations_are_first_class_observations` | implemented |
| Repositories and releases | `sources/software/github.py` | record counts; release/version relationships | implemented |
| Packages and maintainers | `sources/software/packages.py` | `test_package_maintainers_are_contributions_not_aliases` | implemented |
| Dependencies across ecosystems | package and repository adapters | `test_dependency_edges_cross_registries` | implemented |
| Models, datasets, and Spaces remain distinct | `sources/ai/huggingface.py` | `test_huggingface_work_types_and_relationships_remain_distinct` | implemented |
| GitHub numeric IDs stable; handles/full names mutable | GitHub adapter identifiers | rename and transfer tests | implemented |
| Software Heritage IDs identify archived objects | SWH adapter | `test_software_heritage_ids_are_intrinsic_global_identifiers` | implemented |
| Registry maintainers are relationships, not aliases | package contributions | maintainer semantics test | implemented |
| Organisations first-class | account typing in GitHub/HF adapters | organisation test | implemented |
| Popularity metrics timestamped, no universal score | adapter metric helpers; envelope validator | `test_metrics_are_timestamped_observations_not_rank` | implemented |
| Every record carries source receipt, rights, hash, evidence, raw pointer | envelope constructor/validator | all-record validation; manifest fixture hashes | implemented |
| Account rename case | GitHub fixture | rename continuity test | implemented |
| Repository transfer case | GitHub fixture | repository transfer test | implemented |
| Organisation account case | GitHub/HF fixtures | organisation test | implemented |
| Co-maintainers | PyPI fixture | two contribution assertions | implemented |
| Package dependency case | PyPI/Cargo/ecosyste.ms fixtures | dependency test | implemented |
| Archived repository and abandoned Work | GitHub/package fixtures | archived/abandoned test and metrics | implemented |
| Model–dataset–Space relationship | HF fixture | typed relationship test | implemented |
| Source conflict | PyPI/ecosyste.ms fixture | conflict preservation test | implemented |
| Bounded current/bulk-friendly sources | method cards and pilot cost profiles | source ledger and metrics JSON | documented |
| Evaluate public GitHub projects before reinventing | `public-project-evaluation.md` | project/license/adoption table | documented |
| Replayable fixtures and exporter | fixtures; `sources/software/pilot.py` | deterministic export test; manifest digest | implemented |
| Measure stable IDs, edges, events, conflicts, rights, cost | `pilot-metrics.json/.md` | expected metric assertions | implemented for fixture; production cost documented only |
| Compare API-heavy with snapshots/indexes | method cards; cost profiles | explicit acquisition and scale recommendations | documented |
| At least five evidence-first questions | `evidence-first-questions.md` | document review | implemented (documentation) |
| Offline tests | `tests/sources_software_ai/test_pilot.py` | network connection patched to fail; 18 tests passed | implemented |
| No large clone/data commit | fixture sizes and PR diff | manifest and changed-file review | implemented |
| Source rights/update/deletion handling | method cards; source ledger; handoff | source-by-source review | documented; production enforcement deferred |
| Draft PR with required sections | PR #2 | GitHub PR metadata | implemented |
| Production online cohort | not in lane | no production calls/coverage claims | deferred by design |
| Accepted identity precision | identity lane owns decisions | eight literal receipts, zero merges | deferred by design |
| Direct npm adapter | ecosyste.ms supplies pilot npm coverage | cost profile says deferred | deferred pending measured gap |

## Acceptance summary

The branch satisfies the Prompt 10 acceptance target as an offline observation
pilot. It does not claim production-scale coverage, online API costs, accepted
identity precision, or a production ingestion path. Those are explicit gaps,
not hidden implementation omissions.
