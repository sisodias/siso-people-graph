# Source matrix and scale decisions

Reviewed 2026-08-06. The machine-readable form is `source-policies.json`. Terms can change; a production run must re-check the linked official source before collection.

| Source | Stable source-native joins | Main value | Rights / retention boundary | Refresh and removal | Decision |
| --- | --- | --- | --- | --- | --- |
| Publisher RSS + Podcasting 2.0 | feed URL, podcast GUID, item GUID, explicit `podcast:person@href` | shows, episodes, hosts, guests, interviewers, transcript/media pointers | publisher-specific; metadata/evidence by default; media and transcript bodies separately gated | conditional GET; do not infer deletion from truncated feeds alone | `pilot_now` |
| Podcast Index API | feed/episode/person IDs where supplied | discovery and feed reconciliation | restricted; response cache headers govern API material; no permanent API corpus | expire cache; prefer publisher RSS for durable replay | `discovery_only` |
| YouTube Data API | channel ID, video ID | channel accounts, videos, publication relationships | restricted API data; no transcript/video corpus, no cross-platform scoring | refresh/delete stored API data within current 30-day policy unless an explicit exception applies | `research_more` |
| Open Library | author/work/edition keys | modern books, editions, author aliases and roles | public bibliographic metadata; linked text rights separate | pin API/dump snapshot and source-replace by key | `pilot_now` |
| Crossref | DOI and member/source metadata | technical books/papers, contributor order/roles, publication dates | metadata facts by default; abstracts and supplied content may be copyrighted | update by DOI/timestamp; retain correction/retraction lineage | `pilot_now` |
| OpenAlex | author/work IDs, DOI, ORCID, ROR | authority bridges, affiliations, Works, topics/citations | open metadata; API key/credit policy; snapshot preferred for bulk | quarterly/dated snapshot source replacement | `pilot_now` |
| OpenReview | public note/profile IDs | technical papers, venues, public profile/author evidence | public metadata only; readers/licence fields govern visibility/reuse | refresh revisions; honour withdrawals and access changes | `pilot_now` |
| Public pretalx schedules | event/talk/person GUIDs, schedule version | conferences, talks, speakers, temporal appearances | event-publisher terms; public schedule only; no private proposal fields | compare versioned schedules and preserve cancellation/update lineage | `pilot_now` |
| Explicit public-page JSON-LD | page URL, `@id`, `sameAs`, ORCID/DOI when literal | author pages, articles/newsletters/courses, explicit identity receipts | discovery-only by default; site terms/robots govern raw HTML | re-fetch explicit pages only; tombstone removed links/pages | `discovery_only` |

## Explicit exclusions

Reddit, X, LinkedIn, Goodreads, Google Scholar, and similar publicly viewable services are not persistent pilot corpora. They remain discovery-only unless current explicit access and reuse rights support the exact records, retention window, deletion method, and publication purpose. The lane contains no adapters for those services.

## Official references

- Podcasting 2.0 namespace and person/transcript tags: <https://github.com/Podcastindex-org/podcast-namespace>
- Podcast Index legal terms: <https://github.com/Podcastindex-org/legal/blob/master/TERMS.md>
- YouTube API developer policies: <https://developers.google.com/youtube/terms/developer-policies>
- Open Library developer APIs and dumps: <https://openlibrary.org/developers/api> and <https://openlibrary.org/developers/dumps>
- Crossref REST API and metadata licensing: <https://www.crossref.org/documentation/retrieve-metadata/rest-api/>
- OpenAlex API/snapshot docs: <https://docs.openalex.org/>
- OpenReview API v2 and terms: <https://docs.openreview.net/reference/api-v2> and <https://openreview.net/legal/terms>
- pretalx public API: <https://docs.pretalx.org/api/fundamentals/>
- schema.org `sameAs`: <https://schema.org/sameAs>
