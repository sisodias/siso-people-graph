# Scale verdict

## Promote to the next bounded pilot

1. **Publisher RSS + Podcasting 2.0 person metadata.** Best next source. It supplies explicit roles and profile links at low cost, with publisher-origin evidence and ordinary HTTP update semantics.
2. **Open Library + Crossref + OpenAlex.** Use source-native Work/authority IDs to connect modern technical authors to books and papers; use snapshots/dumps for bulk reproducibility.
3. **OpenReview and public conference schedules.** High-value appearances and Works for living researchers, with versioned source records.

## Keep constrained

- **YouTube Data API:** useful stable account/video IDs, but current storage/refresh and cross-platform restrictions require a narrow, quota-budgeted collector. Do not use title/handle equality as identity evidence.
- **Targeted public JSON-LD:** useful for literal author/`sameAs` receipts, but discovery-only by default and never a broad crawl.

## Do not persist as a corpus

- **Podcast Index API responses:** use within current cache headers for discovery; prefer publisher RSS for durable replay.
- **Audio, video, transcripts, article/newsletter bodies, PDFs, and book text:** require a separate rights-gated acquisition capability.
- **Reddit, X, LinkedIn, Goodreads, Google Scholar, and similar public-facing services:** discovery-only absent exact current access/reuse/deletion rights.

## Kill gates

Stop or revise a source pilot when any of the following holds:

- fewer than 5% of reviewed cohort members gain a literal cross-domain bridge;
- manually reviewed precision for the source's proposed identity signal falls below 0.98 for any automatic-resolution proposal (this lane currently proposes no automatic resolution);
- more than 5% of observations lack a terms revision, rights state, payload digest, or deletion/update workflow;
- API cost/quota projects above the budget while an official snapshot/dump provides equivalent evidence;
- removal cannot be propagated reproducibly;
- the source adds names/row count but not stable IDs, Works, roles, temporal evidence, or decision value.

The current fixture passes contract and retention checks, but it is not evidence that the 250-person production cohort will meet these value gates. That measurement requires a current source snapshot and manual review sample.
