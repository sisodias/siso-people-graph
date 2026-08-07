# Method card: conferences and explicit public-web metadata

## pretalx/public schedules

The adapter maps one supplied public schedule export into distinct conference-talk/event observations with versioned schedule provenance, speaker roles, times, rooms, tracks, and source-native GUIDs. It excludes emails, private proposals, speaker biographies, recordings, and slides. Event-publisher terms govern the schedule data; pretalx is the transport/format, not a blanket reuse licence.

Refresh by published schedule version. Preserve cancellations and changes as temporal source lineage rather than overwriting history.

Official API references: <https://docs.pretalx.org/api/fundamentals/> and <https://docs.pretalx.org/api/resources/schedules/>.

## Explicit public pages

The JSON-LD adapter parses only a caller-supplied page. It does not crawl. It maps source-native Person/Organisation/CreativeWork/Event/Course-like nodes, preserves literal `@id`, `url`, DOI/ORCID, and `sameAs` values, and emits author/editor/speaker/contributor roles when the page explicitly supplies them.

A `sameAs` or official-site URL is review evidence, not accepted identity. Names, page titles, and biographies cannot bridge identities. The default rights state is `discovery_only`; raw HTML should remain outside Git unless the page terms clearly permit retention.

Official vocabulary reference: <https://schema.org/sameAs>.

## Scale verdict

Public schedules are `pilot_now` per event after terms review. Public-web JSON-LD remains `discovery_only` and should be used for targeted identity receipts, not broad personal-data scraping.
