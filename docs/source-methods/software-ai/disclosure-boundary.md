# Disclosure boundary

This audit package is designed so another engineer or agent can reconstruct the
Prompt 10 implementation from inspectable evidence. It includes the source
brief, requirements, decisions, alternatives, source references, fixtures,
commands, tests, metrics, deterministic-output digest, assumptions, and known
limitations.

It does **not** claim to publish private hidden chain-of-thought. Hidden internal
reasoning is not a reliable engineering artifact: it may contain abandoned
fragments, unverified hypotheses, and implementation-only scratch work. Treating
that material as authoritative would make the repository less reproducible, not
more.

The repository instead publishes the useful, reviewable equivalent:

- decision statements with the problem each decision solves;
- alternatives considered and reasons they were rejected or deferred;
- evidence and source links supporting each externally grounded claim;
- code paths and tests that enforce each invariant;
- exact commands and observed outputs;
- assumptions, uncertainties, failure modes, and reopening conditions;
- a requirement-to-artifact matrix that exposes omissions.

This boundary is not a request to trust the implementer. It is a request to
verify the implementation through artifacts that can be rerun, diffed, tested,
and falsified.
