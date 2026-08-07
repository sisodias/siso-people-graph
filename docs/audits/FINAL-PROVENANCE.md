# Final provenance and reasoning package

This file is the final index for the Prompt 2 forensic lane on
`pg/red-team-fixtures-20260806`.

## What is now in Git

The branch contains:

- the complete user-provided parallel-agent prompt bundle as a lossless gzip
  archive;
- the exact Prompt 2 source as readable UTF-8;
- a readable archive locator and offline decompression command;
- the offline 22-case red-team suite and synthetic fixtures;
- a narrative audit and stable machine-readable findings register;
- a source-evidence ledger linking every finding to source observations,
  invariants, fixtures, results, blast radius, severity, and owning lane;
- requirement/case/finding traceability;
- normalized execution receipts;
- a forensic decision/work log with rejected alternatives, operational
  corrections, commands, limitations, and downstream instructions;
- a lane handoff; and
- two integrity layers: the historical verifier and the final branch-state
  verifier.

## Exact assignment archive

```text
path: docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt.gz
stored bytes: 17889
stored SHA-256: aae7888a6f076588515a8b977f1d25c3508f7bfd3f43fbfaec2af5f8cdec11b1
Git blob: b8750bd65324864897fa11984b938381ad227d91
decoded bytes: 54730
decoded SHA-256: 077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d
```

Decompress it offline:

```bash
python3 - <<'PY'
import gzip
from pathlib import Path
p = Path('docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt.gz')
print(gzip.decompress(p.read_bytes()).decode('utf-8'), end='')
PY
```

Prompt 2 is also committed plain at
`docs/audits/sources/prompt-02-people-graph-red-team.txt` with SHA-256
`5f490d41ebe26f768131ec9d1f08b8ba6c0736a316ed4336250a104a48298f00`.

## Final verification

```bash
python3 tests/red_team/verify_final_package.py
python3 tests/red_team/verify_final_package.py --run
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
```

`verify_final_package.py` is authoritative for the final branch layout. It
validates the gzip source and decoded source hashes, exact Prompt 2, all nine
pinned local production Git blobs, the Book export pin, 14 requirements, 22
cases, 16 findings, severity/blocker/control sets, receipts, narrative coverage,
and optional live non-volatile evidence replay.

Earlier provenance files preserve the chronology of the first packaging pass.
Some refer to the plain `.txt` source path, which is now a readable locator for
the lossless `.txt.gz` archive. This final verifier intentionally accepts that
historical projection while validating the actual archive bytes directly.

## Result

```text
14 supplied requirements
22 executable cases
16 stable findings
PASS=3 XFAIL=19 FAIL=0 XPASS=0 ERROR=0
P0=8 P1=8
source Git blobs matched=9/9
```

Bulk ingestion must remain blocked on:

```text
PGRT-001 PGRT-002 PGRT-003 PGRT-004
PGRT-006 PGRT-009 PGRT-011 PGRT-016
```

## Reasoning disclosure boundary

The repository contains the complete inspectable basis for the result: exact
instructions, pinned source code, hypotheses/invariants, fixtures, observations,
receipts, severity rules, rejected alternatives, corrections, and limitations.
It does not contain private hidden chain-of-thought text. No material finding
relies on such text; another agent can reconstruct or challenge every conclusion
from the committed evidence chain.

## Validation correction retained

An early provisional execution checkout used manually reconstructed production
files. Their Git blob IDs did not match the pinned baseline, so those receipts
were rejected. The final run was performed only after all nine People Graph
source files matched the exact baseline Git blobs. The semantic outcome was
unchanged: 3 PASS, 19 XFAIL, and no unexpected result.
