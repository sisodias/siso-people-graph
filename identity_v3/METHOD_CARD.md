# Method card: People Graph identity resolution v3.1.0

## Intended use

Generate inspectable identity candidates across source-native People Graph rows,
then derive reversible canonical clusters from explicit decisions. The method is
for entity-resolution support, not biometric identification, legal identity
verification, access control, fraud decisions, or automated decisions about a
person's rights or opportunities.

## Identifier policy

The code registry in `identity_v3/registry.py` declares each scheme's category,
scope, uniqueness, mutability, authority, and automatic-resolution eligibility.
The automatic path is deny-by-default.

Eligible examples include GitHub numeric account ID, GitHub node ID, ORCID,
VIAF, ISNI, Wikidata QID, Library of Congress authority ID, OpenAlex author ID,
DBLP PID, and YouTube channel ID. Eligibility means the value may support an
identity candidate; it does not eliminate conflict checks or prove that a human
owns every account represented by the source record.

Mutable handles are aliases. Names, real names, companies, locations, topics,
biographies, websites, follower counts, and other popularity metrics are
attributes or observations. They are never unique person identifiers.
Unregistered schemes are quarantined from automatic resolution.

## Candidate methods and thresholds

| Method | Confidence | Automatic? | Required evidence |
| --- | ---: | --- | --- |
| `shared_external_id` | 0.995 | Yes, if conflict-free | Exact normalized value in an explicitly eligible unique scheme |
| `name_plus_years` | 0.86 | No | Same Unicode comparison key and compatible life dates |
| `exact_name` | 0.52 | No | Same Unicode comparison key |
| `surname_initial` | 0.35 | No | Same surname/initial, compatible dates, different origins |

Confidence values are policy labels for triage, not calibrated posterior
probabilities. Every candidate also carries literal positive evidence, negative
evidence, conflict reasons, and method version `identity-v3.1.0`.

## Automatic acceptance policy

An automatic decision is permitted only when all conditions hold:

1. the candidate method is `shared_external_id`;
2. the matched scheme is registered as unique and auto-resolution eligible;
3. the pair has no human/organisation, life-date, or conflicting-identifier flag;
4. joining the two existing clusters would not introduce two active values for
   the same unique identifier scheme;
5. there is no active rejection for the candidate.

Repeated acceptance is idempotent. An active opposite decision must be undone
before review state can change. Cluster membership is recomputed from active
accepted decisions, so undo never deletes source rows.

## Unicode and aliases

Name comparison uses NFKC plus Unicode case folding while retaining letters,
numbers, and combining marks from every script. It does not transliterate to
ASCII. The key is never used as a canonical ID. Opaque platform identifiers that
may be case-sensitive are preserved exactly.

GitHub logins are time-bounded aliases linked to the stable numeric GitHub ID.
When the API returns a different login, the old active alias is closed at the
observation time and the new alias becomes active.

## Synthetic evaluation

Command:

```bash
PYTHONPATH=. python3 tests/identity_v3/measure_precision.py
```

Fixture: 20 synthetic entities covering common names, shared employer/city,
personal-looking organisation accounts, account rename, pseudonym, non-Latin
names, one human across platforms, two people sharing a name, and an impossible
transitive cluster.

Measured result:

- 6 automatic candidates: 4 labeled true positives, 0 labeled false positives,
  and 2 deliberately conflict-only pairs; labeled precision `4/4 = 1.000`.
- Applying the automatic policy accepted 5 pair decisions and blocked 1 decision
  because it would create conflicting ORCIDs; the resulting clusters passed the
  invariant audit.
- 6 review-only candidates: 1 true positive and 5 known-distinct pairs; candidate
  precision `1/6 = 0.166667`. These candidates are hypotheses and never automatic
  decisions.

These are adversarial fixture measurements, not production precision estimates.
Production release gates need a stratified, manually reviewed sample by method,
source pair, language/script, entity kind, and account age.

## Known blind spots

- Authority records can merge or split upstream, and one source identifier can
  occasionally refer to a work, account, organisation, pseudonym, or historical
  cluster rather than one natural person.
- Shared stable IDs can reflect source corruption, account transfers, compromised
  accounts, institutional ownership, or identifier reuse. Transitive conflict
  checks reduce but do not eliminate this risk.
- Pseudonym-to-person links may be `same_as`, `operated_by`, or contextual rather
  than unconditional identity. Reviewers must preserve the intended relation.
- Sparse records often lack negative evidence. Missing dates or affiliations are
  not proof of sameness.
- Unicode-preserving comparison avoids ASCII erasure but does not solve
  transliteration, tokenization, patronymics, name order, or culturally specific
  naming conventions.
- Canonical selection is deterministic policy, not a claim that one source row is
  intrinsically more truthful. It currently prefers registry/curated rows, then
  authority/book/platform origins, strong-ID count, and lexical ID.
- The v2 compatibility table still stores attributes in `external_ids`; the new
  matcher registry prevents those rows from acting as identifiers, but a future
  schema should separate them physically.

## Review requirements

Reviewers should inspect literal identifier evidence, source authority, validity
time, entity kind, conflicting stable identifiers, life dates, alias history,
and source-removal obligations. Name-only and surname-initial candidates require
independent corroboration before acceptance.
