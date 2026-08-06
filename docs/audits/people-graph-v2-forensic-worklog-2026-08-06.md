# People Graph v2 forensic decision record and reproducibility worklog

**Audit date:** 2026-08-06  
**Primary baseline:** `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Lane branch:** `pg/red-team-fixtures-20260806`  
**Draft PR:** `sisodias/siso-people-graph#1`

## What this record is

This is the durable, evidence-backed reconstruction of how the red-team result
was produced. It is intentionally more useful than a verbatim private model
scratchpad: every material conclusion is expressed as a chain that another
agent can rerun and falsify:

```text
assignment constraint
  -> pinned source observation
  -> explicit invariant/hypothesis
  -> tiny offline fixture
  -> actual result and evidence
  -> stable finding and severity
```

A hidden chain-of-thought transcript is not treated as evidence and is not
published. The source prompt, inspected code blobs, fixtures, commands, raw
normalized receipts, result-to-requirement mapping, decisions, alternatives,
and uncertainties are all published here or in the adjacent machine-readable
artifacts. No material finding depends on an undocumented intuition.

## Published evidence package

- Original user-provided program bundle: `docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt`
- Exact Prompt 2 slice: `docs/audits/sources/prompt-02-people-graph-red-team.txt`
- Pinned code/source manifest: `docs/audits/people-graph-v2-source-manifest.json`
- Machine-readable assignment contract: `tests/red_team/fixtures/prompt_2_contract.json`
- Requirement/case/finding map: `docs/audits/people-graph-v2-traceability.json`
- Source → invariant → fixture → result → decision ledger: `docs/audits/source-evidence-ledger.json`
- Human receipt: `docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.txt`
- Machine receipt: `docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.json`
- Stable findings: `docs/audits/people-graph-v2-findings.json`
- Narrative audit: `docs/audits/people-graph-v2-red-team-2026-08-06.md`
- Lane handoff: `docs/handoffs/red-team.md`
- Integrity checker: `tests/red_team/verify_audit.py`
- Integrity/replay receipt: `docs/audits/receipts/people-graph-v2-audit-integrity-2026-08-06.txt`

## 1. Scope lock before investigation

The Prompt 2 assignment was first converted into non-negotiable operating
constraints:

1. Work only in `sisodias/siso-people-graph`; treat Book Library and Great
   Library as read-only context.
2. Use the exact branch `pg/red-team-fixtures-20260806`.
3. Change only `tests/red_team/**`, `docs/audits/**`, and
   `docs/handoffs/red-team.md`.
4. Diagnose current `main`; do not fix schema, loaders, query code, README, or
   root configuration.
5. Reproduce every claim with a tiny local fixture, no production asset, no
   network, and Python standard library only.
6. Encode known failures honestly as expected failures rather than weakening
   assertions to make the suite appear green.

The People Graph baseline was pinned to
`de048bb3b34bf931b56fd741cb46c1334acdfb98`. At lane launch there were no open
PRs in that repository. The Book export seam was pinned independently to
`be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b` / blob
`de4e9fd91c076fd514887c82bd334dde43271d7b`.

## 2. Source inspection strategy

The inspection was deliberately seam-first rather than repository-wide
speculation. The assignment named failure families, so the corresponding
production entry points were pinned and read in full:

- build topology and source reconstruction: `build_people_graph_v2.py`,
  `build_people_graph_books.py`, and the v2 DDL;
- identity evidence and persistence: `match_identities.py`, `enrich_owners.py`,
  `external_ids`, and `identity_claim`;
- source replay: owner/topic loaders and Book export;
- canonical reads and absence semantics: `ask.py`;
- temporal derivation: `v_contemporaries`;
- cross-repository attribution: the exact Book export blob.

The complete commit/blob inventory is machine-readable in the source manifest.
The Great Library commit is retained as program context, but no finding is
derived from Great Library content.

## 3. Requirement decomposition

Prompt 2 contained fourteen required investigation areas. They were expanded
into twenty-two cases because several requirements contain distinct invariants
that must fail or pass independently.

| Requirement | Cases | Findings | Requested question |
| --- | --- | --- | --- |
| PGRT-R01 | PGRT-T001 | PGRT-001 | Whether build_people_graph_v2.py finds its schema from a clean checkout. |
| PGRT-R02 | PGRT-T002 | PGRT-002 | Whether the builder silently merges unrelated people on normalized name. |
| PGRT-R03 | PGRT-T003 | PGRT-003 | Whether shared_external_id can treat company, location, real name, or another non-unique attribute as near-certain identity evidence. |
| PGRT-R04 | PGRT-T004 | PGRT-004 | Whether accepted identity claims affect canonical query results or remain inert. |
| PGRT-R05 | PGRT-T005, PGRT-T006, PGRT-T007, PGRT-T008, PGRT-T009, PGRT-T010, PGRT-T011 | PGRT-005, PGRT-006, PGRT-007, PGRT-011, PGRT-013 | Whether each loader is idempotent across two runs: no repeated rank additions, duplicate claims, stale edges, or unrelated-field mutation. |
| PGRT-R06 | PGRT-T012 | PGRT-008 | Whether topics/enrichment work for a canonical entity whose ID is not gh:* or whose origin is not github. |
| PGRT-R07 | PGRT-T013 | PGRT-009 | Unicode/non-Latin name preservation and collision behavior. |
| PGRT-R08 | PGRT-T014 | PGRT-010 | Whether aliases/raw variants reach FTS search. |
| PGRT-R09 | PGRT-T008, PGRT-T015 | PGRT-011 | GitHub account rename and repository-transfer behavior when stable numeric IDs exist. |
| PGRT-R10 | PGRT-T003, PGRT-T016, PGRT-T017 | PGRT-003, PGRT-012 | Ambiguous common names, shared employers, shared locations, organisations with human-looking names, and pseudonyms. |
| PGRT-R11 | PGRT-T006, PGRT-T010, PGRT-T018 | PGRT-013 | Whether rank_score currently mixes incompatible units. |
| PGRT-R12 | PGRT-T019 | PGRT-014 | Whether the current v_contemporaries assumptions create implausible results for unknown death years. |
| PGRT-R13 | PGRT-T020 | PGRT-015 | Whether query inventory and missing-domain behavior can mislead a caller. |
| PGRT-R14 | PGRT-T021, PGRT-T022 | PGRT-016 | Cross-repo assumptions from the Book Library export that can corrupt People Graph attribution or roles. |

This expansion avoids a common testing failure: one broad test can stop at its
first assertion and hide later defects. Separate cases also let implementation
lanes convert one `XFAIL` to `PASS` without erasing a still-open sibling issue.

## 4. Fixture architecture

The suite imports production modules by tracked file path and creates every
SQLite input/output in a fresh temporary directory. The fixture support layer
provides only:

- deterministic schema/bootstrap helpers;
- tiny source databases with the minimum columns each production loader reads;
- subprocess invocation for real CLI/build entry points;
- injected network responses for enrichment, with no live HTTP;
- structured evidence returned by each case.

No copied production database, corpus row, release asset, credential, or live
profile payload is used. The adversarial labels and records are synthetic. The
Book contract fixture stores only public source-code behavior and exact pins.

## 5. Runner semantics

Each case returns `(invariant_holds, evidence)`. The runner combines that with
its declared expectation:

| Declared expectation | Invariant result | Status | Process meaning |
| --- | --- | --- | --- |
| `PASS` | true | `PASS` | confirmed control |
| `PASS` | false | `FAIL` | unexpected regression |
| `EXPECTED_FAILURE` | false | `XFAIL` | known defect reproduced |
| `EXPECTED_FAILURE` | true | `XPASS` | implementation changed; audit is stale |
| either | exception | `ERROR` | fixture or execution failure |

Only all-`PASS`/`XFAIL` runs exit zero. This makes documented current defects
green without allowing a fix, regression, or broken fixture to pass silently.

## 6. Case inventory and final observed state

| Case | Status | Expectation | Finding | Test |
| --- | --- | --- | --- | --- |
| PGRT-T001 | XFAIL | EXPECTED_FAILURE | PGRT-001 | v2 builder resolves its schema from a clean checkout |
| PGRT-T002 | XFAIL | EXPECTED_FAILURE | PGRT-002 | v2 builder does not silently merge normalized names |
| PGRT-T003 | XFAIL | EXPECTED_FAILURE | PGRT-003 | non-unique profile attributes cannot auto-resolve identity |
| PGRT-T004 | XFAIL | EXPECTED_FAILURE | PGRT-004 | accepted identity claims affect canonical reads |
| PGRT-T005 | XFAIL | EXPECTED_FAILURE | PGRT-005 | identity matcher is idempotent across two runs |
| PGRT-T006 | XFAIL | EXPECTED_FAILURE | PGRT-006, PGRT-013 | topic loader is idempotent across two runs |
| PGRT-T007 | PASS | PASS | control | owner loader exact rerun remains duplicate-free |
| PGRT-T008 | XFAIL | EXPECTED_FAILURE | PGRT-006, PGRT-011 | owner loader removes or tombstones stale source rows |
| PGRT-T009 | XFAIL | EXPECTED_FAILURE | PGRT-006 | book-person builder removes stale source rows |
| PGRT-T010 | XFAIL | EXPECTED_FAILURE | PGRT-007, PGRT-013 | GitHub enrichment preserves unrelated canonical fields |
| PGRT-T011 | XFAIL | EXPECTED_FAILURE | PGRT-007 | GitHub enrichment fills each missing field independently |
| PGRT-T012 | XFAIL | EXPECTED_FAILURE | PGRT-008 | topics and enrichment follow non-gh canonical IDs |
| PGRT-T013 | XFAIL | EXPECTED_FAILURE | PGRT-009 | Unicode names survive identity-key construction |
| PGRT-T014 | XFAIL | EXPECTED_FAILURE | PGRT-010 | raw aliases reach FTS search |
| PGRT-T015 | XFAIL | EXPECTED_FAILURE | PGRT-011 | GitHub rename resolves through stable numeric account ID |
| PGRT-T016 | PASS | PASS | control | ambiguous common names remain review-only |
| PGRT-T017 | XFAIL | EXPECTED_FAILURE | PGRT-012 | kind and pseudonym conflicts gate name candidates |
| PGRT-T018 | XFAIL | EXPECTED_FAILURE | PGRT-013 | rank_score has one stable semantic unit |
| PGRT-T019 | XFAIL | EXPECTED_FAILURE | PGRT-014 | unknown death years do not create certain contemporaries |
| PGRT-T020 | XFAIL | EXPECTED_FAILURE | PGRT-015 | missing domains are explicit in query output |
| PGRT-T021 | XFAIL | EXPECTED_FAILURE | PGRT-016 | Book Library export preserves identity boundaries and roles |
| PGRT-T022 | PASS | PASS | control | v2 builder preserves supplied Book contributor roles |

Final counts:

```text
PASS=3
XFAIL=19
FAIL=0
XPASS=0
ERROR=0
TOTAL=22
```

The three controls are intentional:

- `PGRT-T007` proves exact owner-loader replay already avoids duplicate rows.
- `PGRT-T016` proves exact-name matching is currently proposed at 0.55 rather
  than auto-accepted.
- `PGRT-T022` proves v2 preserves distinct Book roles when upstream supplies
  them, isolating role loss to the pinned Book export seam.

## 7. How findings were derived

A finding was created only when all of these existed:

1. a pinned production file/function or pinned cross-repository contract;
2. a stated invariant independent of the current implementation;
3. a fixture executing the real code path;
4. structured evidence showing the actual state;
5. a reproduction command;
6. a bounded blast-radius statement; and
7. an owning lane capable of fixing the named seam.

| Finding | Severity | Cases | Bulk blocker | Title |
| --- | --- | --- | --- | --- |
| PGRT-001 | P0 | PGRT-T001 | yes | Clean-checkout v2 build cannot locate the tracked schema |
| PGRT-002 | P0 | PGRT-T002 | yes | v2 build silently merges source-native people by normalized display name |
| PGRT-003 | P0 | PGRT-T003 | yes | Non-unique profile attributes are eligible for 0.98 identity auto-acceptance |
| PGRT-004 | P0 | PGRT-T004 | yes | Accepted identity claims are inert in canonical reads |
| PGRT-005 | P1 | PGRT-T005 | no | Identity matcher reruns duplicate claims |
| PGRT-006 | P0 | PGRT-T006, PGRT-T008, PGRT-T009 | yes | Loaders are additive rather than source-replaceable |
| PGRT-007 | P1 | PGRT-T010, PGRT-T011 | no | GitHub enrichment overwrites canonical fields and blocks partial refresh |
| PGRT-008 | P1 | PGRT-T012 | no | Topics and enrichment do not follow GitHub identity to non-gh canonical IDs |
| PGRT-009 | P0 | PGRT-T013 | yes | Book identity keys collapse distinct non-Latin names |
| PGRT-010 | P1 | PGRT-T014 | no | Retained book aliases are discarded before FTS population |
| PGRT-011 | P0 | PGRT-T008, PGRT-T015 | yes | GitHub login changes and repository transfers split identity despite stored numeric IDs |
| PGRT-012 | P1 | PGRT-T017 | no | Name candidates ignore human, organisation, and pseudonym conflicts |
| PGRT-013 | P1 | PGRT-T006, PGRT-T010, PGRT-T018 | no | rank_score mixes and overwrites incompatible units |
| PGRT-014 | P1 | PGRT-T019 | no | v_contemporaries turns unknown death into birth+80 |
| PGRT-015 | P1 | PGRT-T020 | no | Missing-domain results look like evidence-backed empty results |
| PGRT-016 | P0 | PGRT-T021, PGRT-T022 | yes | Pinned Book Library export silently merges names and drops non-author roles |

The narrative audit explains each P0 and P1 in detail. The findings JSON is the
authoritative stable-ID registry.

## 8. Severity decision rule

`P0` in this audit does not mean an active security incident. It means the
observed behavior can corrupt or invalidate bulk construction/identity at scale
and therefore must block bulk ingestion or bulk acceptance until resolved. The
P0 gate was applied when a fixture demonstrated at least one of:

- clean builds cannot start;
- distinct people can be silently fused;
- non-unique attributes can be accepted as near-certain identity;
- accepted identity decisions do not affect canonical reads;
- reruns retain stale source assertions or repeatedly mutate values;
- Unicode source identities collapse;
- stable platform identities split across rename/transfer; or
- cross-repository export loses identity boundaries or contributor roles.

`P1` marks serious correctness, observability, or interpretation defects that
need an owning implementation lane but do not independently justify stopping
all fixture-scale work.

## 9. Key decisions and rejected alternatives

### Diagnose, do not patch production

Rejected: fixing the schema path, identity matcher, loaders, or query behavior in
this lane. That would violate exclusive ownership, mix evidence with remediation,
and conflict with parallel implementation branches. The lane instead creates a
stable executable contract for those fixes.

### Use real production entry points

Rejected: reimplementing production logic inside tests. Reimplementation can
prove only that the test model behaves a certain way. Cases import or invoke the
actual tracked modules and keep fixture DDL minimal.

### Keep expected failures strict

Rejected: marking defective behavior as `PASS`, skipping it, or asserting only
that the current output is stable. The invariant describes the desired safety
property; current violations are `XFAIL`, and unexplained `XPASS` is non-zero.

### Add positive controls

Rejected: a suite containing only failures. Controls prevent future fixes from
removing behavior that is already correct and identify the true seam—for
example, Book role loss upstream rather than in the v2 builder.

### Pin cross-repository behavior by blob

Rejected: copying the Book script or relying on a moving branch. The fixture
records repository, commit, path, blob SHA, and observed contract so later
agents can detect staleness explicitly.

### Treat evidence, not elapsed time, as the result

Elapsed milliseconds vary by environment and are retained only for diagnostics.
Finding status depends solely on the invariant and structured eridence.

## 10. Operational incidents and recoveries

These execution details are recorded so another GitHub/Codex agent can reproduce
the workflow without repeating avoidable connector mistakes:

- A repository-root `fetch_file` attempt failed because the GitHub contents path
  was a directory. Recovery: enumerate exact tracked paths through indexed code
  search/commit metadata and fetch each file directly.
- A generic GitHub fetch attempt rejected a non-contents URL/ref shape. Recovery:
  use `fetch_file(repository, path, ref)` for known repository files.
- The first branch-creation call omitted both `sha` and `base_ref` and was
  rejected. Recovery: create `pg/red-team-fixtures-20260806` from `main`.
- Large connector responses were truncated for display. Recovery: pin blob SHAs,
  reconstruct the clean checkout, parse local artifacts, and compare Git object
  hashes with remote blobs before opening the PR.
- GitHub CLI was unavailable in the execution runtime. Recovery: use the GitHub
  connector for branch, file, and PR writes; use local Python/git hashing for
  validation. No force push or direct-main write was used.

None of these operational corrections changes a finding. They are workflow
notes, not source evidence.

### Validation correction: provisional checkout rejected

During the provenance expansion, the first temporary execution checkout was
found to contain manually reconstructed production files whose Git blob hashes
did not equal the pinned baseline blobs. That checkout was suitable for early
case authoring, but it was not acceptable as final baseline execution evidence.
The discrepancy was treated as a validation failure rather than hidden:

1. the provisional receipts were rejected;
2. every local People Graph source used by the suite, plus `README.md`, was
   reconstructed byte-for-byte from the pinned Git blobs;
3. Git blob object IDs were recomputed locally and compared with the manifest;
4. all nine People Graph source files matched exactly;
5. the full 22-case suite was rerun; and
6. both committed execution receipts were regenerated from that exact checkout.

The exact rerun produced the same semantic result—3 PASS, 19 XFAIL, no FAIL,
XPASS, or ERROR. Only volatile elapsed times and the enrichment run timestamp
changed. This correction is why the integrity checker verifies local Git blob
IDs and can optionally replay all non-volatile evidence with `--run`.

Exact local source verification:

```text
README.md                                      3ae7738eed163cabb72ed5ea4d57d38453ec40f1
schema/people_schema_v2.sql                    07b70a2eaf8db48d741010d2d5f31810a0c9d0d1
loaders/ask.py                                 37e19c92d242bc979eb2ab55b4f6f6a02872083d
loaders/build_people_graph_books.py            08b667b448c3acbc4bc0357f378270d46892e071
loaders/build_people_graph_v2.py               7983db530d242b386fcd3c8277718010b7a43034
loaders/enrich_owners.py                       9ea6956f30a06115b8c5946be02ef2dfffb7208b
loaders/load_owner_topics.py                   f33d0cfc459330fd97fb69865c7cb7da33468e57
loaders/load_owners_into_people_graph.py       726742a7e7dcfe8c0f76107daef0c147f9e42e34
loaders/match_identities.py                    541c68e7083e54327141aaed37f004579b024c4c
```

## 11. Exact validation commands

```bash
python3 -m py_compile \
  tests/red_team/run.py \
  tests/red_team/support.py \
  tests/red_team/cases_build.py \
  tests/red_team/cases_identity.py \
  tests/red_team/cases_loaders.py \
  tests/red_team/verify_audit.py

python3 - <<'PY'
import json
from pathlib import Path
for path in [
    Path('tests/red_team/fixtures/adversarial_people.json'),
    Path('tests/red_team/fixtures/book_library_export_contract.json'),
    Path('docs/audits/people-graph-v2-findings.json'),
    Path('docs/audits/people-graph-v2-source-manifest.json'),
    Path('docs/audits/people-graph-v2-traceability.json'),
    Path('docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.json'),
]:
    json.loads(path.read_text(encoding='utf-8'))
    print('JSON OK', path)
PY

python3 tests/red_team/verify_audit.py
python3 tests/red_team/verify_audit.py --json
python3 tests/red_team/verify_audit.py --run
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
python3 tests/red_team/run.py --list
python3 tests/red_team/run.py --case PGRT-T003 --case PGRT-T004
```

The committed receipts are a normalized capture of the full and JSON commands.
The only normalization replaces the ephemeral local checkout prefix with
`<clean-checkout>`; evidence values are otherwise unchanged.

Receipt digests:

```text
people-graph-v2-red-team-run-2026-08-06.txt  b1d184f745ff18baa4bc5c63b42da81b55e11321d57e1a8001b0e01b4d1a22a4
people-graph-v2-red-team-run-2026-08-06.json 97103d1f0ef3f8211530a2e1ea44acdf791c846ffc0d130e39879dfa9d55b1e6
people-graph-v2-audit-integrity-2026-08-06.txt ac935226eb7c27197f2bb089a1d8f10943c823a158964069ceb363afae58fd80
```


Final integrity/replay result:

```text
source blob matches = 9/9
requirements = 14
cases = 22
findings = 16
static consistency checks = 15/15
live replay checks = 1/1
verifier errors = 0
```

## 12. Publication chronology before this provenance expansion

```text
9ce2533 Test: add adversarial identity fixture
8b928da Test: pin Book Library export contract
9c3dd8b Docs: explain red-team runner semantics
3838cdb Docs: add red-team lane handoff
7ab7aeb Docs: add machine-readable red-team findings
ea0d02c Docs: publish People Graph v2 red-team audit
2acda92 Test: add red-team fixture support
5347bc6 Test: add build and Unicode red-team cases
c35047a Test: add loader and enrichment red-team cases
f351892 Test: add identity and query red-team cases
9dcfa79 Test: add offline People Graph red-team runner
89dfec0 Docs: update red-team changed paths
```

The draft PR was then opened as `#1`, titled
`Test: codify current People Graph failure modes`. This provenance expansion is
additive and remains entirely inside the lane-owned paths.

## 13. Limits and uncertainty

- Tiny fixtures establish reachability and behavior of exact code paths; they do
  not measure production-corpus prevalence.
- The suite does not inspect or modify the released People Graph database.
- The Book fixture can become stale when its pinned blob changes; that is a
  detectable contract update, not an excuse for an unpinned live dependency.
- FTS5 is required by the existing v2 schema and therefore remains an
  environment prerequisite for the corresponding tests.
- A fix may expose a second defect hidden behind the current first failure. Split
  the case rather than weakening its invariant.
- `P0`/`P1` are program merge gates defined above, not universal incident
  response categories.

## 14. Instructions for implementation agents

1. Name the affected `PGRT-*` finding IDs in commits and PR descriptions.
2. Run the single case first, then the full suite.
3. Convert the relevant `XFAIL` to `PASS`; an unexplained `XPASS` is deliberately
   non-zero.
4. Update the narrative audit, findings register, traceability map, and receipts
   in the same change.
5. Preserve the positive controls.
6. Do not delete source evidence to make a failing invariant disappear.
7. Record migration, replacement, rights, and compatibility behavior in the
   owning lane's handoff.
