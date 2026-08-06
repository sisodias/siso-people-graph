# People Graph v3 validation record

**Validation time:** 2026-08-06T16:12:45Z  
**Branch:** `pg/v3-ontology-schema-20260806`  
**Original remote head validated:** `2f66fbe1f4523399463d9e1ff8971879a84f5b88`  
**Base:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`

## Environment

```text
Python 3.13.5
Python sqlite3 module 2.6.0
SQLite runtime 3.46.1
FTS5 compile option detected: true
JSON function probe: true
sqlite3 command-line executable: unavailable in this runner
```

The missing CLI is reported rather than hidden. The committed `.read` manifests
are checked for completeness, while the Python standard-library harness applies
all SQL modules in lexical order using the same content.

## Commands and results

### Lane runner

```bash
python3 tests/schema_v3/run.py
```

```text
Original implementation: 13 schema-invariant tests passed.
Expanded audit packet: 26 total tests passed (13 schema + 13 provenance/audit).
```

### Independent unittest discovery

```bash
python3 -m unittest discover -s tests/schema_v3 -p 'test_*.py' -v
```

```text
26 tests discovered and passed after the audit/provenance packet was consolidated.
```

### Python syntax compilation

```bash
python3 -m py_compile tests/schema_v3/*.py
```

```text
py_compile: ok
```

## Test inventory

The first 13 are schema invariants. The final 13 verify source/prompt hashes, public reasoning and decision/requirement completeness, lane/path and payload safety, runtime declarations, machine-manifest consistency, full-file SHA-256 receipts, and relative-link integrity.

```text
test_artifact_manifest_matches_every_lane_file
test_decision_record_has_unique_stable_ids
test_machine_provenance_is_parseable_and_pinned
test_no_forbidden_payload_or_out_of_scope_path_is_manifested
test_relative_markdown_links_resolve
test_source_prompt_is_pinned_and_contains_lane_contract
test_every_decision_has_evidence_artifacts_tests_and_rationale
test_every_requirement_is_traceable_and_expected_set_is_present
test_expanded_audit_packet_and_machine_manifests_are_consistent
test_ledger_and_brief_disclose_sources_non_sources_and_limits
test_manifested_artifacts_stay_inside_lane_and_exclude_payload_assets
test_public_reasoning_package_and_source_hashes_are_complete
test_validation_record_matches_the_executable_suite_and_runtime_features
test_envelope_import_cannot_assign_a_canonical_id
test_foreign_keys_reject_orphan_observations
test_rights_privacy_and_publication_coverage
test_schema_and_sample_apply_with_foreign_keys_clean
test_source_observations_and_identity_decisions_are_append_only
test_unicode_and_alias_search_preserve_non_latin_text
test_conflicting_stable_ids_block_identity_acceptance
test_identity_merge_can_be_reversed_without_losing_sources
test_unique_identifiers_are_enforced_within_scope
test_model_output_is_explicit_and_not_source_evidence
test_projections_are_named_versioned_scoped_and_uncertain
test_vocabularies_remain_namespaced_and_crosswalks_explicit
test_work_subtypes_roles_versions_citations_and_dependencies
```

## Fixture application

The ordered nine DDL modules and four sample modules were applied to an in-memory
SQLite database with `PRAGMA foreign_keys=ON`.

```text
foreign_key_check []
integrity_check ok
source: 2
source_snapshot: 2
observation_envelope_receipt: 1
source_observation: 7
observation_identifier: 2
entity: 7
entity_alias: 2
entity_identifier: 1
work: 2
work_version: 2
contribution: 1
evidence: 5
identity_candidate: 1
identity_decision: 1
identity_cluster: 1
entity_redirect: 1
assertion: 2
relationship: 1
projection_run: 1
projection_value: 1
ddl_modules: 9
sample_modules: 4
```

Bundle digests hash the exact UTF-8 text executed by `support.py::_bundle`: modules in lexical order joined by one newline:

```text
ddl_bundle_sha256    9f9fa374c8e0607d195858ad158a2e53b2db325bca9b4802d86bf4299b16eff7
sample_bundle_sha256 6891a156a487fe077e5a4bca6158a6045d87d1c92377894210b39bd079c576bf
```

## Original implementation file hashes

These hashes describe the original 24-file implementation commit before this
audit packet was appended:

```text
465a32e09868fb1227644c4d49ab5d3b1bed482bce4eea745eb0b41a25032db3  docs/architecture/people-graph-v3.md
89ad619ff44ea2ec2a2bcf17424a00b9f4fe7600d55facfb923db81605dee9f5  docs/handoffs/schema-v3.md
2fcfeae1aa14991df4f02b47c4fbd902d702dcdb06e6d45bae38193f0c5dcbde  schema/v3/README.md
6ba7b78c0623fa4e59f98a0cc54a7f91045dead6177d0bf6b93ce8fe04f213f1  schema/v3/ddl/00_metadata_policy.sql
831b36ccecf111180447e22ce82d7f24a9fcc4ef018f01bc9c38c5cbaee9520b  schema/v3/ddl/10_source_observations.sql
2cc7a6f64406d2ff02040c798365a58ca15b652becc68d7f7f2b4ed355c17e1b  schema/v3/ddl/20_observation_semantics.sql
f17d12d667fa93cf8ba74a70cdf27a682caff214259ac023da272f67e637bf0b  schema/v3/ddl/30_entities_and_search.sql
7cc08d7eebd79f879f72fa905acb6a3048f13540ce547b9ed9ceb2cb6e9021a5  schema/v3/ddl/40_works.sql
b69933b82cc310b689dc1a5093d50b676bcf4a59731964758a96835a48b54c4a  schema/v3/ddl/50_vocabularies.sql
e0bacc013b41ca852bdfc0ae6292c4fdcdf782458802f58f224ac1fe18417cc2  schema/v3/ddl/60_evidence_and_identity.sql
db31def9f8c2e28e2cee36ec85af78df6cf2f74a83c9694fc452a4f9f11f9201  schema/v3/ddl/70_assertions_relationships.sql
e491d9761bea2bc3419f399d18c726b851ee71b002c7d62fa903aa841ffbe2be  schema/v3/ddl/80_projections.sql
0452ccf8c04f049b2d859d9f7f92de3bbf2875a3bfd7750f822cc66ba10ca901  schema/v3/observation-envelope-mapping.md
edbeca4e43657c8ab2c785d7a73c7991d89a7b3629897cb355293bf92d4ef0ce  schema/v3/people_graph_v3.sql
f75edbf6a9b3bc2287dd04fbffe09d3fc74d38c311049253d2325c2efd5e5af9  schema/v3/sample/00_observations.sql
dedecaf97eadc5cbb0aaf4c1e90311502761c9e191570b98be82dcaef41b3867  schema/v3/sample/10_entities_and_works.sql
69212e9438c924a71eed00168d6719ab2eb70000990d241c37d5a194abe239a8  schema/v3/sample/20_evidence_and_identity.sql
bcf5d71b9a3b12354e225d2afffdc2bc15851e79364b28764f00aab4cd6adc0a  schema/v3/sample/30_claims_relationships_projections.sql
d2ac0b87ffc909ee2488f425ff34c7d864a4753843f68a57afec592156312354  schema/v3/sample_data.sql
fbca7f52f5509a69c561632c51ca371d693ffb275822e0d90b8d64433fa74c1a  tests/schema_v3/run.py
a5da1993adf95b7825fcff8d18e33bb30b16cde82a093fa0d044c3468cc98776  tests/schema_v3/support.py
435e6372565b591b698b1e30d366ef427ff09d1c683f40654fc486070087a13c  tests/schema_v3/test_schema_core.py
ae969300af33c51cc0b206ee03f7a7b39d0989879be17c8330cfb4c8ada969a7  tests/schema_v3/test_schema_identity.py
9f81fd836e891908a2daa6d35bfccebe9dd40b51d134f7041e856b7128482532  tests/schema_v3/test_schema_works.py
```

## Remote verification

The remote architecture blob was re-fetched from the branch and had Git blob SHA
`1daf83669331b5d045b81b2a6396032ad2077b34`, matching the local original file.
GitHub reported PR #3 open, draft, and mergeable, with head
`2f66fbe1f4523399463d9e1ff8971879a84f5b88`, 24 changed files, 2,077 additions,
and zero deletions at the time this validation began.

No GitHub Actions workflow run was associated with the original commit. The
reported test results are therefore local/offline results, not CI results.

## Path and data-safety scan

The implementation and audit follow-up contain only Markdown, JSON, SHA-256 manifests, SQL, and Python source inside the assigned owned paths. Scans found:

```text
forbidden SQLite/database/archive/key extensions: none
private topology markers (/Volumes, /Users, /home): none
credential-like PEM/API-key/password markers: none
production payloads: none
```

Compiled `__pycache__` files were generated locally during validation and were
not part of the GitHub commit.

## What this validation does not prove

- performance or storage behavior at 10× observations;
- full logical/binary reproducibility of a production build;
- correctness of source-specific rights decisions;
- candidate-generation recall or identity precision;
- query/API compatibility after integration;
- source adapter conformance beyond the synthetic envelope;
- locale-aware search beyond tested Unicode FTS behavior;
- that the unified Work-version model is sufficient for every domain.

These are explicit adoption gates, not silent assumptions.
