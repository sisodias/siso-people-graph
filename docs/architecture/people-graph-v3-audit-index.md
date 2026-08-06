# People Graph v3 audit and reverse-engineering packet

This is the public engineering record for the additive People Graph v3 schema
proposal. A reviewer can reconstruct the inputs, observations, design choices,
implementation sequence, validation, limitations, and integration seams without
chat history or access to a private scratchpad.

## Transparency boundary

This packet publishes the exact assignment, pinned sources, source-derived facts,
bounded inferences, stable decisions, rejected alternatives, chronology, commands,
outputs, tests, hashes, known unknowns, and review gates. It intentionally does
not publish private token-by-token model chain-of-thought, credentials,
authentication material, or unrelated scratch data. The published record is the
checkable engineering rationale an independent agent needs.

## Reading order

### 1. Contract and source receipts

1. [`people-graph-v3-source-prompt.md`](people-graph-v3-source-prompt.md) — exact shared launch rules, `pg-observation-0.1`, and Prompt 3 with source digests.
2. [`people-graph-v3-agent-brief.md`](people-graph-v3-agent-brief.md) — compact preserved operator brief for this lane.
3. [`people-graph-v3-assignment.md`](people-graph-v3-assignment.md) — Prompt 3-only contract and integrity receipt.
4. [`people-graph-v3-source-ledger.md`](people-graph-v3-source-ledger.md) — compact, machine-tested source inventory and explicit non-sources.
5. [`people-graph-v3-evidence-ledger.md`](people-graph-v3-evidence-ledger.md) — detailed pinned evidence and observation→inference→decision traces, including official SQLite references.

### 2. Reasoning and decisions

6. [`people-graph-v3-design-journal.md`](people-graph-v3-design-journal.md) — chronological public deductions, alternatives, tradeoffs, and seams.
7. [`people-graph-v3-engineering-record.md`](people-graph-v3-engineering-record.md) — source audit, implementation sequence, and bounded reasoning summary.
8. [`people-graph-v3-decision-log.md`](people-graph-v3-decision-log.md) — compact decisions, alternatives, consequences, and open questions.
9. [`people-graph-v3-decision-record.md`](people-graph-v3-decision-record.md) — stable `PGV3-D###` records with confidence, evidence, tests, and reversal triggers.
10. [`people-graph-v3-worklog.md`](people-graph-v3-worklog.md) — reproducible procedure, command history, tooling limits, and deliberately unperformed work.

### 3. Traceability and inventories

11. [`people-graph-v3-traceability.md`](people-graph-v3-traceability.md) — compact requirement/decision-to-artifact/test map.
12. [`people-graph-v3-requirements-traceability.md`](people-graph-v3-requirements-traceability.md) — expanded requirement and invariant coverage.
13. [`people-graph-v3-schema-inventory.md`](people-graph-v3-schema-inventory.md) — reviewer-oriented object/module inventory.
14. [`../../schema/v3/SCHEMA_INVENTORY.md`](../../schema/v3/SCHEMA_INVENTORY.md) — schema-adjacent inventory, fixture counts, constraints, and test ownership.

### 4. Validation and falsification

15. [`people-graph-v3-validation-record.md`](people-graph-v3-validation-record.md) — exact runtime, commands, test inventory, integrity results, bundle digests, original file hashes, and non-claims.
16. [`people-graph-v3-independent-review.md`](people-graph-v3-independent-review.md) — adversarial checks and adoption gates for a fresh reviewer.
17. [`../../tests/schema_v3/run.py`](../../tests/schema_v3/run.py) — offline runner.
18. [`../../tests/schema_v3/test_audit_package.py`](../../tests/schema_v3/test_audit_package.py) and [`../../tests/schema_v3/test_design_provenance.py`](../../tests/schema_v3/test_design_provenance.py) — executable audit/provenance checks.

### 5. Machine-readable receipts

19. [`../../schema/v3/PROVENANCE.json`](../../schema/v3/PROVENANCE.json) — master source, decision, compatibility, validation, and artifact record.
20. [`../../schema/v3/design_provenance.json`](../../schema/v3/design_provenance.json) — detailed source/decision/requirement graph enforced by tests.
21. [`../../schema/v3/traceability.json`](../../schema/v3/traceability.json) — compact requirements, SQLite references, validation, and known gaps.
22. [`../../schema/v3/ARTIFACTS.sha256`](../../schema/v3/ARTIFACTS.sha256) — SHA-256 for every lane file except the manifest itself.

## Primary implementation

- [`people-graph-v3.md`](people-graph-v3.md) — architecture proposal.
- [`../../schema/v3/README.md`](../../schema/v3/README.md) — schema entry point.
- [`../../schema/v3/people_graph_v3.sql`](../../schema/v3/people_graph_v3.sql) — ordered DDL manifest.
- [`../../schema/v3/sample_data.sql`](../../schema/v3/sample_data.sql) — ordered synthetic fixture manifest.
- [`../handoffs/schema-v3.md`](../handoffs/schema-v3.md) — integration handoff.

## Complementary provenance layers

The `agent-brief`/`source-ledger`/`design-journal`/`traceability` set is compact
and bound to `design_provenance.json`. The `source-prompt`/`evidence-ledger`/
`decision-record`/`worklog` set records a more detailed human-readable audit.
`PROVENANCE.json` and `ARTIFACTS.sha256` bind both sets to exact files. The
overlap is deliberate: compact machine enforcement plus detailed independent
review.

## Data and rights statement

The branch is additive and public-safe. It contains no production SQLite
database, corpus, credential, client data, personal note, private storage
topology, or rights-unclear payload. Sample records are synthetic.
