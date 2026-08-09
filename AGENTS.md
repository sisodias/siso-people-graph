# Agent guide — SISO People Graph

SISO People Graph is an independently addressable Research Work for person,
identity, work, topic, and temporal graph contracts. Its canonical checkout is
this repository, but its mutable databases and source payloads are external
data-plane material.

## Cold start

1. Read `README.md` for the graph's membership rule, schema laws, loader
   surface, and honest limitations.
2. Read `docs/handoffs/identity-resolution.md` and
   `docs/handoffs/schema-v3.md` before changing identity or schema paths.
3. Read `schema/people_schema_v2.sql` before changing graph tables or edges.
4. Use `loaders/ask.py --help` to understand the read-only query surface.
5. Navigate code with the shared Serena fleet first. Use narrow text search only
   if Serena is unavailable; do not begin with a repository-wide scan.

The Great Library identity for this Work is
`gls:work:2b03baa8-6dab-4e91-ab4c-9b8db4543236` (`siso-people-graph`). The
Great Library is the public identity and lineage control plane; it is not the
graph database or a source-payload mirror.

## Boundary and ownership

- This repository owns loader code, schema contracts, query behavior, and
  reproducible-build logic for the People Graph.
- SISO Knowledge governs durable graph and index service semantics without
  absorbing this repository or its databases.
- Foundry may discover and evaluate source universes and emit observations; it
  is not canonical identity, merge, or claim truth.
- Evidence Engines may transform and adjudicate observations before canonical
  admission.
- Physical checkout placement does not establish ownership or containment.

Do not silently merge identities, flatten topic vocabularies, or represent a
derived dependency edge as a social relationship. Roles belong on edges, and
identity claims must remain explicit, evidenced, and reversible.

## Verification

These non-mutating command forms were observed on this checkout and expose the
actual supported loader interfaces:

```bash
python3 loaders/ask.py --help
python3 loaders/build_people_graph_books.py --help
python3 loaders/build_people_graph_v2.py --help
python3 loaders/load_owners_into_people_graph.py --help
python3 loaders/load_owner_topics.py --help
python3 loaders/enrich_owners.py --help
```

The repository's test command is:

```bash
python3 -m unittest discover -s tests -v
```

On the clean main-based checkout this runs 18 tests successfully. A separate
dirty feature branch was observed with an import-shadowing failure, so always
report the result from the branch actually under review. Loader help commands
are read-only; build and loader commands that accept `--apply` or write an
output database require explicit input/output paths and a deliberate review
before use.

## Generated and protected state

Generated databases, source snapshots, payload archives, private receipts, and
machine-specific locators are not public repository truth. Keep them outside
Git and preserve their owning domain. The existing `.private-recovery`
directory is protected local recovery material; do not inspect, publish, move,
or delete it as routine cleanup. Do not add credentials, tokens, client data,
raw source payloads, or machine topology.

No project-local agent-state directory is part of this checkout. Do not create
shared memory, duplicate registries, or task systems here for routine work. A
resumable multi-agent run requires an explicit project-local contract first;
otherwise leave agent state in the orchestrating system.

## Change discipline

Work from the current branch and preserve unrelated dirty files. Keep schema,
loader, and data-plane changes separate. Verify in this repository before
claiming a handoff, report known failures with their exact command and error,
and never treat a local database count as a verified release fact without a
query receipt and provenance.
