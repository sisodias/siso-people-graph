# Red-team handoff addendum — final provenance package

This addendum extends `docs/handoffs/red-team.md` without rewriting the original
handoff chronology.

## Final added paths

```text
docs/audits/FINAL-PROVENANCE.md
docs/audits/people-graph-v2-final-provenance.json
docs/audits/WORKLOG-ERRATA.md
docs/audits/HANDOFF-ADDENDUM.md
docs/audits/receipts/people-graph-v2-final-package-integrity-2026-08-06.txt
tests/red_team/verify_final_package.py
```

The exact full assignment source is stored at:

```text
docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt.gz
```

Its decoded SHA-256 is
`077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d`.

## Authoritative validation

```bash
python3 tests/red_team/verify_final_package.py
python3 tests/red_team/verify_final_package.py --run
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
```

Final validation state:

```text
static final-package checks: 10/10
live replay checks: 11/11
verifier errors: 0
PASS=3 XFAIL=19 FAIL=0 XPASS=0 ERROR=0
```

## Integration note

The repository now contains the complete inspectable evidence chain needed to
reverse-engineer every material conclusion: assignment, pinned source blobs,
invariants, fixtures, results, stable findings, severity rules, alternatives,
corrections, and limitations. It intentionally does not publish private hidden
chain-of-thought text; no conclusion relies on it.

Review `FINAL-PROVENANCE.md`, then run the authoritative verifier before merging
or implementing any named `PGRT-*` seam.
