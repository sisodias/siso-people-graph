# Reconstruction index

Start here to reverse-engineer Prompt 10 without guessing intent.

## Source and boundaries

1. `prompt-10-source.md` — verbatim relevant source brief.
2. `disclosure-boundary.md` — what is and is not represented as engineering
   reasoning.
3. `docs/handoffs/software-ai-pilot.md` — lane scope, paths, assumptions,
   compatibility seams, risks, data/rights notes, and merge guidance.

## Rationale and traceability

4. `decision-log.md` — decisions, alternatives, evidence, consequences, and
   reopening conditions.
5. `engineering-walkthrough.md` — input-to-output derivation, architecture,
   source transformations, worked example, metric formulas, verification,
   limitations, and extension protocol.
6. `requirement-traceability.md` — every material Prompt 10 requirement mapped to
   code, fixtures, tests, metrics, documentation, or a deliberate deferment.

## External evidence

7. `source-ledger.md` — official source links, facts used, pilot inferences,
   rights/update boundaries, and refresh triggers.
8. `method-cards.md` — acquisition, identifier, cost, rights, deletion/update,
   promote, and kill criteria by source.
9. `public-project-evaluation.md` — license/reuse decisions for public projects.

## Executable implementation

10. `sources/software/envelope.py` — interim observation contract, safety
    validator, canonical JSON, deterministic NDJSON.
11. `sources/software/github.py` — GitHub REST and GH Archive adapters.
12. `sources/software/packages.py` — PyPI, crates.io, and ecosyste.ms adapters.
13. `sources/software/software_heritage.py` — Software Heritage adapter.
14. `sources/ai/huggingface.py` — Hugging Face adapter.
15. `sources/software/pilot.py` — fixture orchestration, exporter, validator,
    metrics, and source cost profiles.

## Replay evidence

16. `tests/sources_software_ai/fixtures/*.json` — tiny synthetic adversarial raw
    fixtures.
17. `tests/sources_software_ai/test_pilot.py` — offline contract and adapter
    assertions.
18. `pilot-manifest.json` — fixture hashes and logical-output digest.
19. `pilot-metrics.json` and `pilot-metrics.md` — machine/human measured results.
20. `verification-log.md` — exact commands, observed outcomes, test coverage,
    and interpretation boundary.
21. `evidence-first-questions.md` — example questions impossible to answer from a
    star ranking alone.

## Minimal reproduction

```bash
PYTHONPATH=. python -m unittest discover -s tests/sources_software_ai -v
PYTHONPATH=. python -m sources.software.pilot export \
  --fixtures tests/sources_software_ai/fixtures \
  --out /tmp/software-ai.ndjson \
  --metrics-out /tmp/software-ai-metrics.json
PYTHONPATH=. python -m sources.software.pilot validate /tmp/software-ai.ndjson
sha256sum /tmp/software-ai.ndjson
```

Expected implementation-run digest:
`f1e5b923f22b6e94f9102bda2abc4c33f0bfd3bd8ed03b8fc903dee745b5780e`.

## Review order

For a fast audit, read: source brief → requirement matrix → decision log →
validator → tests → manifest/metrics → source ledger → handoff. For a design
audit, add the walkthrough and method cards. For a rights audit, begin with the
source ledger and method cards, then inspect fixture terms/rights receipts.
