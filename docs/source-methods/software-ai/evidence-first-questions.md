# Evidence-first questions star rankings cannot answer

Each question below requires typed relationships, temporal observations,
source-native identifiers, or provenance. Sorting repositories by stars cannot
answer it reliably.

1. **Which repository survived an account rename and later moved to an
   organisation without losing continuity?** Follow the stable numeric
   repository ID across mutable `full_name` observations and the
   `transferred_from` edge.
2. **Which package release can be traced to a source repository, a specific
   checksum, its runtime dependencies, and an archived source revision?** Join a
   versioned PURL, SHA-256, `version_of`, `depends_on`, `source_repository`, and
   SWHID observations.
3. **Which organisations are first-class maintainers across GitHub, a package
   registry, and Hugging Face rather than being mistaken for people?** Compare
   typed organisation observations and contribution edges using literal stable
   source identifiers.
4. **Which model was trained on which dataset and is actually used by which
   Space at a particular revision?** Traverse `trained_on`, `uses_model`, and
   `uses_dataset` edges while retaining model, dataset, and Space types.
5. **Which high-download package is abandoned even though downstream packages
   still depend on it?** Combine timestamped download/dependent metrics with the
   explicit `abandoned` state and dependency edges.
6. **Where do sources disagree on a package’s license, and what literal records
   produced the disagreement?** Group source observations by PURL and preserve
   contradictory licenses for review instead of picking the most popular source.
7. **Who co-maintained a release across registries and repositories, and what
   evidence supports each platform link?** Inspect contribution roles and
   cross-platform stable-ID receipts; do not collapse matching display names.
8. **What happened after an archived repository’s last release?** Compare the
   release time, GH Archive events, live archived state, and Software Heritage
   visit/revision observations.

The synthetic pilot fixtures exercise all eight question shapes. They prove the
contract can represent the evidence; they do not claim production answers for
real people or projects.
