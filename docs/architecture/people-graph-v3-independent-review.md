# People Graph v3 independent review and falsification checklist

A reviewer should try to break the proposal rather than merely confirm that the
fixture passes. Record results in a new review or follow-up PR; do not weaken the
invariants to make a test green.

## Assignment and scope

- **IR-01:** Diff the branch against its base and prove every path is owned by the
  ontology/schema lane.
- **IR-02:** Confirm no existing v2 file, root README/config, loader, query file,
  production asset, or generated surface changed.
- **IR-03:** Compare the exact assignment copy with the operator brief hash.

## Source/observation integrity

- **IR-04:** Attempt to import names, employer, location, biography, topic, and a
  mutable login as globally unique identity identifiers. The interface/policy
  must reject or keep them non-unique.
- **IR-05:** Insert an envelope with a top-level, subject-level, or disguised
  canonical ID. Extend checks/import validation if a bypass is found.
- **IR-06:** Attempt update/delete of receipts and observations, then model legal
  removal through status/tombstone events.
- **IR-07:** Create two snapshots with the same source revision but different
  digests and decide whether the current uniqueness rule is correct.
- **IR-08:** Test a source that cannot legally retain the full receipt JSON; prove
  a minimized content-addressed receipt can still satisfy audit/removal needs.

## Identifier and identity safety

- **IR-09:** Use two entities with different accepted ORCIDs/VIAF IDs and a shared
  name, employer, city, website hostname, and mutable handle. Acceptance must be
  blocked until the stable conflict is explicitly resolved.
- **IR-10:** Test global, source, and organisation scopes with identical values.
- **IR-11:** Test identifier retirement, reassignment, and temporal alias history.
- **IR-12:** Build a transitive A=B, B=C cluster where A and C have conflicting
  stable IDs. The identity engine must detect the conflict before materializing
  the cluster.
- **IR-13:** Revoke an accepted decision twice and verify idempotent deterministic
  undo semantics in the future identity implementation.
- **IR-14:** Determine whether canonical entity labels need multi-evidence accepted
  assertions instead of one `label_observation_id`.

## Works and attribution

- **IR-15:** Model one Work with original expression, translation, edition,
  software release, dataset version, and manifestation. Decide whether unified
  `work_version` is semantically adequate.
- **IR-16:** Preserve multiple roles and ordering for the same contributor/Work;
  include editor, translator, illustrator, maintainer, host, guest, and
  institutional contributor.
- **IR-17:** Test citation/dependency edges when the cited/depended-on Work is only
  a source observation and not yet canonical.
- **IR-18:** Test Work split and merge reversal without losing locators or roles.

## Evidence, claims, and relationships

- **IR-19:** Attempt to mark model output as literal source evidence.
- **IR-20:** Create accepted, contested, withdrawn, and superseded claims with
  supporting and challenging evidence.
- **IR-21:** Verify valid time versus observed time for affiliations, handle
  changes, authorship corrections, and posthumous publications.
- **IR-22:** Test rights/publication filtering when supporting evidence has a more
  restrictive state than the assertion.
- **IR-23:** Decide whether assertion and relationship policy states should be
  computed from evidence or explicitly adjudicated.

## Search and internationalization

- **IR-24:** Test Arabic, Chinese, Japanese, Cyrillic, Devanagari, diacritics,
  apostrophes, hyphens, emoji, combining characters, and multiple scripts.
- **IR-25:** Prove FTS maintenance after alias/entity updates and deletes.
- **IR-26:** Benchmark exact identifier lookup separately from fuzzy/discovery
  search; no fuzzy result may imply identity.

## Scale and rebuild

- **IR-27:** Generate at least 10× current observation counts in a synthetic or
  lawful pilot and measure DDL application, index build, query plans, storage,
  WAL behavior, and integrity-check cost.
- **IR-28:** Compare one-file SQLite, attached observation shards, and an external
  columnar observation plane while preserving the logical contract.
- **IR-29:** Run two clean source-declared builds and compare logical digests and
  row counts; report binary SQLite differences honestly.
- **IR-30:** Test snapshot replacement, tombstones, and stale-edge removal.

## Integration and release gates

- **IR-31:** Import a real `pg-observation-0.1` fixture from each source lane with
  no canonical entity created by import.
- **IR-32:** Capability-detect v2/v3 from the query lane and label ambiguity,
  provenance, policy, and inference state.
- **IR-33:** Run the integration contract harness against any subset of parallel
  PRs and document abstraction duplication or path conflicts.
- **IR-34:** Require a source/rights manifest, logical digest, validation report,
  and rollback/cutover plan before any production v3 asset is published.
- **IR-35:** Keep `3.0.0-draft.1` until identity, build, query, source, Book, and
  claims pilots have challenged the model.

## Review outcome template

```text
Review date:
Reviewer/agent:
Base/head commits:
Checks attempted:
Passed:
Failed:
New counterexamples:
Schema changes proposed:
Policy/rights issues:
Performance measurements:
Merge recommendation: accept | revise | reject | split
```
