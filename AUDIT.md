# Architecture audit entry point

The 2026-08-06 first-principles re-derivation is preserved as an auditable package:

- [`docs/first-principles/README.md`](docs/first-principles/README.md) — complete derivation, findings, alternatives, uncertainties, target model, and execution order.
- [`docs/first-principles/evidence-ledger.json`](docs/first-principles/evidence-ledger.json) — machine-readable sources, findings, reproductions, confidence, proposals, and unresolved questions.
- [`tools/verify_audit_findings.py`](tools/verify_audit_findings.py) — bounded executable checks for the schema path, FTS behavior, identity-matcher semantics, query contract, score ambiguity, and related findings.
- [`docs/first-principles/agent-program.md`](docs/first-principles/agent-program.md) — non-overlapping agent lanes, ready-to-paste prompts, acceptance gates, kill gates, and merge order.

Run:

```bash
python3 tools/verify_audit_findings.py
```

The audit distinguishes current observations from reproduced behavior, architectural inference, proposals, and unknowns. Future agents should update the evidence ledger when a finding is repaired rather than deleting the historical reasoning that motivated the change.
