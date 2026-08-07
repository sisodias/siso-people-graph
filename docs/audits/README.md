# People Graph v2 red-team evidence index

This directory contains the complete Prompt 2 forensic package for
`sisodias/siso-people-graph` at baseline
`de048bb3b34bf931b56fd741cb46c1334acdfb98`.

## Recommended reading order

1. `people-graph-v2-red-team-2026-08-06.md` — findings and blast radius.
2. `people-graph-v2-forensic-worklog-2026-08-06.md` — full evidence-backed
   reconstruction of the investigation and decisions.
3. `tests/red_team/fixtures/prompt_2_contract.json` — machine-readable assignment contract.
4. `people-graph-v2-traceability.json` — exact requirement/case/finding map.
5. `source-evidence-ledger.json` — reconstructible evidence/decision chain per finding.
6. `people-graph-v2-source-manifest.json` — commit/blob/digest provenance.
7. `people-graph-v2-findings.json` — stable machine-readable finding registry.
8. `receipts/` — normalized execution outputs plus
   `people-graph-v2-audit-integrity-2026-08-06.txt` (16 checks, zero errors).
9. `sources/` — exact user-provided assignment source.
10. `tests/red_team/verify_audit.py` — offline cross-artifact and replay checker.

## Reproduce

```bash
python3 tests/red_team/verify_audit.py
python3 tests/red_team/verify_audit.py --run
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
python3 tests/red_team/run.py --list
```

Expected audited-baseline result:

```text
PASS=3 XFAIL=19 FAIL=0 XPASS=0 ERROR=0 TOTAL=22
```

## Evidence hierarchy

Material claims should be checked in this order:

1. pinned source file/commit/blob;
2. invariant stated by the executable case;
3. tiny fixture and production code path;
4. normalized run receipt;
5. stable finding projection.

The forensic worklog is an auditable reasoning reconstruction, not a verbatim
private model chain-of-thought. No finding relies on undisclosed scratchpad text.

## Rights and safety

Fixtures are synthetic and tiny. The package contains no production database,
release asset, corpus text, credential, private profile payload, live API
response, or private filesystem topology. The prompt bundle is user-provided
project material explicitly requested for publication.
