# Method card: modern books and scholarly sources

## Open Library

The adapter emits author, Work, and edition observations separately, preserving Open Library keys, aliases, edition-to-Work relations, contributor evidence, and source timestamps. It never assumes an Open Library author record and a GitHub account are the same person. Bulk scale should use a pinned Open Library dump rather than harvesting the API.

Official references: <https://openlibrary.org/developers/api> and <https://openlibrary.org/developers/dumps>.

## Crossref

The adapter emits DOI-addressed Works with contributor order/roles and source metadata. Crossref metadata is used as metadata; abstracts/full text are excluded unless a separate field-level licence permits retention. Use the polite pool/mailto, caching, and backoff.

Official references: <https://www.crossref.org/documentation/retrieve-metadata/rest-api/> and <https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-metadata-license-information/>.

## OpenAlex

The adapter emits OpenAlex author and Work observations, including literal DOI, ORCID, ROR, and other source-linked IDs where present. It preserves source conflicts rather than silently choosing one affiliation/title/date. The API currently requires a key and metered credits; a pinned OpenAlex snapshot is the preferred reproducible bulk path.

Official references: <https://docs.openalex.org/> and <https://docs.openalex.org/download-all-data/openalex-snapshot>.

## OpenReview

The adapter emits public API v2 notes as source-native Works, retaining note ID, venue/invitation context, public contributor IDs, licence/readers evidence, and modification time. It does not ingest PDFs or private fields, and it treats withdrawal/access changes as source updates.

Official references: <https://docs.openreview.net/reference/api-v2> and <https://openreview.net/legal/terms>.

## Scale verdict

`pilot_now` for bounded source-native metadata. The highest-value joins are explicit ORCID/DOI/OpenAlex/OpenReview/Open Library keys and linked official pages; names remain review hints only.
