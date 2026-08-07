# Forensic worklog errata and final-layout note

This append-only note preserves the chronology of the first provenance packaging
pass while making the final branch layout unambiguous.

## Corrections

- In `people-graph-v2-forensic-worklog-2026-08-06.md`, the word `eridence` in
  “Treat evidence, not elapsed time, as the result” is a typographical error;
  read it as `evidence`.
- The exact 54,730-byte user-provided prompt bundle is authoritative in the
  lossless gzip archive
  `sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt.gz`.
  The same-name `.txt` file is a readable locator and decompression recipe, not
  the original bundle bytes.
- The archive SHA-256 is
  `aae7888a6f076588515a8b977f1d25c3508f7bfd3f43fbfaec2af5f8cdec11b1`;
  its decoded SHA-256 is
  `077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d`.
- `tests/red_team/verify_final_package.py` is authoritative for the final branch
  layout. `verify_audit.py` and the first source manifest remain committed as
  historical projections of the earlier plain-path packaging pass.
- The final integrity/replay receipt is
  `receipts/people-graph-v2-final-package-integrity-2026-08-06.txt`.

No finding, severity, blocker, control, source pin, or executable result changed
because of these packaging corrections.
