# Rights, refresh, removal, and retention workflow

The source-policy registry is executable in `sources/media/policies.py` and exported as `source-policies.json`. A collector must re-check current official terms before a production run.

## Common workflow

1. Record the exact endpoint/feed/page, terms revision, retrieval time, source observation time, response revision/ETag where available, and SHA-256 of the replayable payload.
2. Store full raw payloads outside Git. Tiny, public-safe fixtures are the only exception.
3. Apply the source-specific retention boundary before writing an observation.
4. Rebuild source observations from a new pinned snapshot. Do not mutate unrelated source rows or canonical entities.
5. Preserve corrections, redirects, withdrawals, and tombstone receipts. Never delete the original evidence history merely because a canonical decision changes.
6. Remove or restrict publication when a source record becomes private, is deleted, or its reuse basis no longer supports the publication state.

## Source-specific rules

- **RSS:** conditional GET; source-replace by feed/GUID; absence from a rolling feed is not deletion by itself.
- **Podcast Index:** cache-header bounded; expire/purge API material; publisher RSS is the preferred durable source.
- **YouTube:** refresh/delete stored API data within the current policy window; delete unavailable source fields; retain only permitted evidence receipts.
- **Open Library:** source-replace from a pinned API/dump snapshot; preserve redirects/tombstones by key.
- **Crossref:** update by DOI and source timestamp; preserve correction/retraction lineage; exclude copyrighted content without a licence.
- **OpenAlex:** source-replace from a dated API/snapshot receipt; preserve redirects and source conflicts.
- **OpenReview:** refresh note/profile revisions and readers/licence fields; honour withdrawals and access changes.
- **pretalx:** compare published schedule versions; preserve cancellation/time/room changes.
- **Public web:** refresh only explicit pages under site policy; remove/tombstone when a literal identity assertion is removed or the page returns 404/410.

## Media/transcript gate

A metadata observation may point to a media or transcript URL, but acquisition is a separate capability requiring an explicit licence/rights decision, payload manifest, deletion workflow, and publication state. This PR commits no transcript, audio, video, PDF, article body, newsletter body, or book payload.
