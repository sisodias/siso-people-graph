# Method card: Podcast Index

## Purpose

Use Podcast Index as a discovery and reconciliation source for feeds/episodes and source-native IDs. The adapter accepts a saved API response and emits cache-bounded observations. It also provides the documented SHA-1 authentication-header recipe for a collector, but performs no network request itself.

## Rights boundary

The current terms reviewed for this lane are Podcast Index Terms of Service v1.1 dated 2021-03-02: <https://github.com/Podcastindex-org/legal/blob/master/TERMS.md>. The pilot therefore marks observations `restricted`, records a cache-header retention boundary, and does not treat API responses as a permanent reusable corpus.

No audio, transcript, or media payload is acquired. Durable replay should come from the independent publisher RSS feed when available.

## Update/removal

- Obey API response cache/rate headers.
- Expire cached responses at the permitted boundary.
- Purge cached API material on termination or when otherwise required by current terms.
- Preserve only evidence receipts and source-native pointers permitted by the exact run.

## Scale verdict

`discovery_only`. It is useful for finding feeds and reconciling Podcast Index IDs, but it is not the default durable data plane.
