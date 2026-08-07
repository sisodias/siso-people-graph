# Method card: publisher RSS and Podcasting 2.0

## Purpose

Create source-native observations for podcasts, shows, episodes, hosts, guests, interviewers, and other publisher-declared contributor roles. The adapter accepts a supplied RSS/Atom payload and performs no network I/O.

## Observed records

- Channel/feed becomes a `work` with `work_type: podcast_show`.
- Item/entry becomes a distinct `work` with `work_type: podcast_episode`.
- `podcast:person` rows become contribution edges. The adapter preserves the source role string and order.
- A person `href` becomes an `official_website` identifier with literal XML-field evidence. A label without `href` remains name-only evidence and cannot create a bridge.
- Item-level people replace channel contributors when present; otherwise the show contributors are copied with their original receipts.
- Enclosure and `podcast:transcript` values become rights-gated pointers, never acquired media/transcript content.

## Update/removal

Use conditional GET with `ETag` and `Last-Modified`. Identify the client and obey publisher cache/rate rules. Do not treat an item disappearing from a rolling/truncated feed as a deletion. A source tombstone requires an explicit removal signal, stable-GUID change, repeated complete-snapshot evidence, HTTP 404/410, or publisher confirmation.

## Scale verdict

`pilot_now`. This is the best next source for overlap because it can carry explicit roles and profile URLs from the publisher without an API credential. Pilot source lists must still be rights-reviewed feed by feed.
