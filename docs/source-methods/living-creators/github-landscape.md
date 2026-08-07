# Public GitHub project review

Reviewed 2026-08-06. No third-party source code was copied into this lane.

| Project | Licence reviewed | Reusable idea | Decision |
| --- | --- | --- | --- |
| `kurtmckee/feedparser` | BSD-style permissive licence in repository `LICENSE` | mature RSS/Atom edge-case handling | Keep the stdlib fixture adapter dependency-free now; adopt `feedparser` for production only after pinning a version and adding malformed-feed fixtures. |
| `scrapinghub/extruct` | BSD-3-Clause | JSON-LD/microdata/RDFa extraction | Current adapter intentionally supports supplied JSON-LD only. Adopt `extruct` later if microdata/RDFa materially improves explicit identity evidence. |
| `pretalx/pretalx` | current code AGPLv3 with additional terms; docs have separate licensing | versioned public schedule API and stable event/talk identities | Consume the public API; do not vendor or copy application code. Event-publisher data terms remain separate. |
| `OpenReview/openreview-py` | MIT | maintained API client and OpenReview object semantics | Optional client for a network collector; fixture adapter stays pure mapping code. |
| `schemaorg/schemaorg` | Apache-2.0 repository | vocabulary definitions, especially `sameAs` | Use the vocabulary semantics; no code dependency required. |

The implementation uses Python standard-library XML/HTML/JSON tooling so all tests remain offline and dependency-free. That is an isolation choice, not a claim that the small parsers cover every malformed real-world feed or page.
