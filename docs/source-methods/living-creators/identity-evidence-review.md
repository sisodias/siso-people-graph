# Identity-evidence review

This lane proposes candidates; it never merges or canonically resolves them.

## Accepted evidence classes for candidate generation

1. Shared stable, unique authority IDs: ORCID, VIAF, ISNI, or Wikidata. These are labelled `strong` but still require the identity lane's conflict checks and explicit decision.
2. Shared literal `sameAs` or official-site URLs. These are `review_only`; site ownership, link direction, redirects, and account/operator boundaries must be inspected.
3. Source account IDs remain source-scoped. A cross-source reuse is an audit conflict, not a bridge.

Name equality, surname/initial similarity, employer, location, topic, biography, follower count, and handle similarity produce no candidate.

## Fixture review result

The offline fixture run produced four candidates:

- one shared authority-ID candidate spanning five source domains;
- three shared explicit-link candidates spanning two source domains each;
- zero automatic acceptances.

The fixture supplied four manual labels. Two candidates were accepted, both were labelled the same entity, and fixture precision was therefore 1.0. This number validates measurement plumbing only. It is not a production estimate because the fixture was designed to include clear positive and negative cases.

## Production review gate

Before scale-up, draw a stratified sample by signal type and source pair. Review literal receipts, negative evidence, conflicting stable IDs, organisation/person boundaries, pseudonyms, link direction, and time validity. Report precision with sample size and confidence interval. Do not accept a candidate because its label resembles an existing People Graph name.
