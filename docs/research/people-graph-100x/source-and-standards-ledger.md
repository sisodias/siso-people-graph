# Source and standards ledger

**Cut:** 2026-08-06  
**Purpose:** make every load-bearing observation and external design input discoverable without relying on chat history  

## Evidence classes

| Class | Meaning |
| --- | --- |
| `R1` | exact repository code or schema at a pinned commit/blob |
| `R2` | deterministic fixture, validation result or draft PR artifact |
| `R3` | official external standard, API, dump or policy documentation |
| `R4` | inference derived from R1–R3 and explicitly labelled as inference |

This ledger does not claim that every external source is approved for ingestion. The current ingestion decision for each source belongs to the 39-source matrix in Great Library draft PR #2.

# Repository evidence

## SISO People Graph baseline

Repository: <https://github.com/sisodias/siso-people-graph>  
Commit: `de048bb3b34bf931b56fd741cb46c1334acdfb98`

| Path | Blob observed | Why it matters |
| --- | --- | --- |
| `README.md` | `3ae7738eed163cabb72ed5ea4d57d38453ec40f1` | stated mission, counts, roles, identity policy, derived-data rule and cross-domain limitation |
| `schema/people_schema_v2.sql` | `07b70a2eaf8db48d741010d2d5f31810a0c9d0d1` | actor, external ID, content, claim, topic, search and contemporaries contracts |
| `loaders/build_people_graph_v2.py` | `7983db530d242b386fcd3c8277718010b7a43034` | clean-build path, name reuse, life-date, topic and FTS behavior |
| `loaders/match_identities.py` | `541c68e7083e54327141aaed37f004579b024c4c` | normalization, claim methods, confidence and persistence behavior |
| `loaders/ask.py` | `37e19c92d242bc979eb2ab55b4f6f6a02872083d` | current read-only query surface and capability behavior |
| `loaders/enrich_owners.py` | inspected through repository search and red-team evidence | GitHub profile observations, field overwrite and identifier semantics |
| `loaders/load_owner_topics.py` | inspected through red-team evidence | replay and rank-score behavior |
| `loaders/load_owners_into_people_graph.py` | inspected through red-team evidence | mutable login/full-name identity and ownership behavior |
| `loaders/build_people_graph_books.py` | inspected through red-team evidence | ASCII key behavior and stale-output behavior |

Canonical file URLs use the pinned commit, for example:

- <https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/schema/people_schema_v2.sql>
- <https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/loaders/build_people_graph_v2.py>
- <https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/loaders/match_identities.py>
- <https://github.com/sisodias/siso-people-graph/blob/de048bb3b34bf931b56fd741cb46c1334acdfb98/loaders/ask.py>

## SISO Book Library baseline

Repository: <https://github.com/sisodias/siso-book-library>  
Commit: `be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`

| Path | Blob observed | Why it matters |
| --- | --- | --- |
| `README.md` | `d72203f0776d6b012081a02c3b4900c25f5fbfa3` | index/payload split, byte ranges, roles, rights prose and quality gates |
| `scripts/build_books_module.py` | `d912a3c74aad53fcf9a14c0dfa546ffd8a168d27` | Gutenberg source rows, classifications and blanket run-level rights default |
| `scripts/build_people_graph.py` | `08b667b448c3acbc4bc0357f378270d46892e071` | author parsing, role extraction, corporate heuristic and ASCII person keys |
| `scripts/load_into_people_graph.py` | `de4e9fd91c076fd514887c82bd334dde43271d7b` as pinned by red-team PR | cross-repository identity reuse and role-loss seam |

Canonical file examples:

- <https://github.com/sisodias/siso-book-library/blob/be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b/scripts/build_books_module.py>
- <https://github.com/sisodias/siso-book-library/blob/be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b/scripts/build_people_graph.py>

## Great Library baseline and research model

Repository: <https://github.com/sisodias/great-library-of-siso>  
Reviewed main baseline used by the parallel program: `12f4cc249b2b5dc268d05d1698fe9c5e3079327d`

| Path | Blob observed | Why it matters |
| --- | --- | --- |
| `README.md` | `a282231b50f17de88a3f4ed11f704a858bc909ef` | registry boundaries and Research/Frontier Question model |
| `AGENTS.md` | `c524d59797d3716359c4043847b9cb239abcd372` | cold-start, source-of-truth and append-only lane contract |
| `CONTRIBUTING.md` | `23d6d74dd9475f023ebb899936ab3e172214b459` | source, rights, publication safety and verification rules |
| `CURRENT_STATE.md` | `0f4eeed988ddc83fbe56bdc4598d83a8d21372f5` | selected state, known boundaries and resume points |
| `docs/question-driven-research.html` | `2ec1c5f688fa25402d4cab71cd46f8500e8b4adb` | Source Cards, Claims, Assumptions, Experiments and Answer Releases |
| `schemas/common.schema.json` | `f3f388ec62dca59b27ff585eb9f1a8e5ced45fc2` | current evidence, ownership, locator and relationship vocabulary |
| `schemas/work.schema.json` | `f92615fe911aaa3b3312ce7f0859dbf4e7e55478` | Work types and Frontier Question research contract |
| `schemas/release.schema.json` | `3bc43b2d863af172ca98e8fd87fb9f63f20155d7` | Release, answer type and artifact/distribution contract |
| `schemas/god-question-program.schema.json` | `d812a3fc32e58b91602134726375b098b3f9185c` | assumptions, evidence connections and action-learning links |
| `site/intelligence.json` | `6a5ca042795f0d84e3826ebe83760c0216e0aca5` | observed zero active initiatives on the then-generated main projection |

# Live draft work used as evidence

Draft status means the artifacts are inspectable but not accepted into `main`.

| Repository | PR | Branch | Head | Evidence used |
| --- | ---: | --- | --- | --- |
| People Graph | [#1](https://github.com/sisodias/siso-people-graph/pull/1) | `pg/red-team-fixtures-20260806` | `89dfec07acc38c6dadba69547a7ad4d60fbccf15` | 22 offline cases; 16 findings; 8 P0/8 P1 |
| People Graph | [#2](https://github.com/sisodias/siso-people-graph/pull/2) | `pg/software-ai-pilot-20260806` | `b78ff6704783dff100774063c305011ce456d704` | source-observation envelope fixtures and software/AI adapter decisions |
| People Graph | [#3](https://github.com/sisodias/siso-people-graph/pull/3) | `pg/v3-ontology-schema-20260806` | `2f66fbe1f4523399463d9e1ff8971879a84f5b88` | additive v3 evidence ontology and 13 invariant tests |
| Great Library | [#1](https://github.com/sisodias/great-library-of-siso/pull/1) | `gls/people-graph-parallel-spine-20260806` | `215cf63a320523f9c6405b17ae64ddb5468fb2f1` | ADR-0005, GQ-010, observation envelope and thirteen lane reservations |
| Great Library | [#2](https://github.com/sisodias/great-library-of-siso/pull/2) | `gls/people-graph-source-research-20260806` | `20dc000451c28c707b0a97b943d1a4b178ea9bf0` | 39-source matrix, rights/deletion matrix, value theses and pilot portfolio |

# External source-research delegation

The detailed source-specific assessment lives in Great Library draft PR #2:

- `research/people-graph-sources/source-matrix.json`
- `research/people-graph-sources/source-matrix.md`
- `research/people-graph-sources/rights-and-deletion-matrix.md`
- `research/people-graph-sources/github-landscape.md`
- `research/people-graph-sources/100x-value-theses.md`
- `research/people-graph-sources/pilot-portfolio.md`
- `research/people-graph-sources/handoff.md`

At its pinned head it covers **39 sources** with **19 `pilot_now`, 8 `research_more`, 6 `discovery_only` and 6 `do_not_ingest`**. Each record includes owner, access, identifiers, record types, scale, freshness, snapshot/delta behavior, terms revision, rights, attribution, quota, deletion, privacy, reproducibility, overlap hypothesis, information gain, cost, kill condition and state.

The source list and official entry points are preserved below for discovery. The state in the matrix controls whether a source is suitable for persistent ingestion.

## Scholarly, authority and bibliographic sources

| Source | Official entry point |
| --- | --- |
| OpenAlex | <https://developers.openalex.org/> |
| Crossref public data and REST metadata | <https://www.crossref.org/services/metadata-retrieval/public-data-file/> |
| ORCID public data | <https://info.orcid.org/public-data-file-use-policy/> |
| DBLP | <https://dblp.org/> |
| OpenReview API v2 | <https://docs.openreview.net/reference/api-v2> |
| Research Organization Registry | <https://ror.org/data/> |
| Wikidata data downloads | <https://www.wikidata.org/wiki/Wikidata:Database_download> |
| Library of Congress Linked Data Service | <https://id.loc.gov/> |
| Open Library dumps | <https://openlibrary.org/developers/dumps> |
| OpenCitations | <https://opencitations.net/> |
| VIAF data | <https://viaf.org/viaf/data/> |

## Software and AI sources

| Source | Official entry point |
| --- | --- |
| GitHub REST/GraphQL APIs | <https://docs.github.com/en/rest> |
| Hugging Face Hub API | <https://huggingface.co/docs/hub/api> |
| PyPI Index API | <https://docs.pypi.org/api/index-api/> |
| ecosyste.ms API | <https://ecosyste.ms/api> |
| npm registry API | <https://github.com/npm/registry/blob/master/docs/REGISTRY-API.md> |
| crates.io data access | <https://crates.io/data-access> |
| Software Heritage | <https://www.softwareheritage.org/> |
| GH Archive | <https://www.gharchive.org/> |

## Creators and media

| Source | Official entry point |
| --- | --- |
| RSS 2.0 specification | <https://www.rssboard.org/rss-specification> |
| Podcast Index API | <https://podcastindex-org.github.io/docs-api/> |
| Podcast Namespace | <https://github.com/Podcastindex-org/podcast-namespace> |
| YouTube Data API v3 | <https://developers.google.com/youtube/v3> |
| pretalx schedule API | <https://docs.pretalx.org/api/resources/schedules.html> |
| schema.org `sameAs` | <https://schema.org/sameAs> |

## Public discourse

| Source | Official entry point |
| --- | --- |
| AT Protocol repository specification | <https://atproto.com/specs/repository> |
| Stack Exchange API | <https://api.stackexchange.com/> |
| Hacker News API | <https://github.com/HackerNews/API> |
| Mastodon API guidance | <https://docs.joinmastodon.org/api/guidelines/> |

## Institutions and economic activity

| Source | Official entry point |
| --- | --- |
| NIH RePORTER API | <https://api.reporter.nih.gov/> |
| SEC EDGAR data access | <https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data> |
| USPTO Open Data Portal | <https://data.uspto.gov/> |
| Companies House API | <https://developer.company-information.service.gov.uk/> |
| OpenCorporates API | <https://api.opencorporates.com/documentation/API-Reference> |

## Restricted or high-risk sources in the current matrix

| Source | Official policy or entry point |
| --- | --- |
| Reddit Data API | <https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki> |
| LinkedIn API terms | <https://www.linkedin.com/legal/l/api-terms-of-use> |
| X developer agreement and policy | <https://developer.x.com/en/developer-terms/agreement-and-policy> |
| Goodreads API notice | <https://www.goodreads.com/api> |
| Google Scholar help | <https://scholar.google.com/intl/us/scholar/help.html> |
| Crunchbase terms | <https://about.crunchbase.com/terms-of-service/> |

The matrix currently places these six in `do_not_ingest`; their potential information value does not override access, rights, deletion, privacy or reproducibility constraints.

# External standards and design inputs

These are model inputs, not automatically adopted specifications.

## Dates and time

- Extended Date/Time Format, Library of Congress: <https://www.loc.gov/standards/datetime/>

Use: uncertain, approximate, open and interval dates. SISO still needs source assertions and bitemporal observation semantics around the representation.

## Bibliographic Works and manifestations

- BIBFRAME 2.0 model: <https://www.loc.gov/bibframe/docs/bibframe2-model.html>

Use: Work/Instance/Item distinctions and bibliographic relationships. Adapt for software, datasets and media rather than copying library terminology wholesale.

## Exact evidence targeting

- W3C Web Annotation Data Model: <https://www.w3.org/TR/annotation-model/>
- IIIF Presentation API 3.0: <https://iiif.io/api/presentation/3.0/>

Use: selectors, text/image/media targets, fragments and annotations. SISO must add source digests, rights state and transform lineage.

## Provenance

- W3C PROV-O: <https://www.w3.org/TR/prov-o/>

Use: entities, activities, agents and derivation lineage. The internal model may remain relational while exporting compatible provenance.

## Contributor roles

- CRediT taxonomy: <https://credit.niso.org/>

Use: richer scholarly contribution roles. The SISO vocabulary must also cover software maintenance, translation, hosting, podcast production and archival roles.

## Citation and argument relations

- Citation Typing Ontology: <https://sparontologies.github.io/cito/current/cito.html>

Use: typed citation intent and relationships. Do not infer citation intent automatically without evidence and model provenance.

## Software identifiers and licensing

- Package URL specification: <https://github.com/package-url/purl-spec>
- SPDX specifications: <https://spdx.dev/specifications/>
- Software Heritage persistent identifiers: <https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html>

Use: package coordinates, license expressions and durable software artifact identity.

## General linked-data interoperability

- schema.org `Person`: <https://schema.org/Person>
- schema.org `CreativeWork`: <https://schema.org/CreativeWork>
- DataCite metadata schema: <https://schema.datacite.org/>

Use: export and source mapping. SISO’s internal identity and evidence rules remain stricter than generic web markup.

# Public open-source systems evaluated as reusable components or pattern libraries

The Great Library source-research branch records detailed adopt/borrow decisions. The principal systems are:

- Splink — probabilistic candidate generation: <https://github.com/moj-analytical-services/splink>
- Dedupe — active-learning entity resolution: <https://github.com/dedupeio/dedupe>
- OpenRefine reconciliation protocol/client patterns: <https://reconciliation-api.github.io/specs/latest/>
- dlt — bounded incremental data transport: <https://github.com/dlt-hub/dlt>
- DuckDB — snapshot profiling and deterministic analysis: <https://duckdb.org/>
- ScanCode Toolkit — software licence and notice receipts: <https://github.com/aboutcode-org/scancode-toolkit>
- RDFLib — RDF/PROV-O/JSON-LD export: <https://github.com/RDFLib/rdflib>
- NetworkX — bounded algorithm/reference tests: <https://networkx.org/>
- DataHub — metadata platform pattern library: <https://github.com/datahub-project/datahub>
- OpenMetadata — metadata/governance pattern library: <https://github.com/open-metadata/OpenMetadata>

DataHub and OpenMetadata are not proposed as a second SISO control plane. Their value is in inspecting mature patterns for lineage, contracts, quality and governance.

# Evidence gaps

The following remain unresolved and should not be presented as sourced facts:

- independently rebuilt current production row counts;
- exact current release-asset availability and checksums;
- production prevalence of each code-path defect;
- measured overlap yield for the proposed scholarly/media pilots;
- source costs beyond directional estimates;
- acceptance of the unmerged Great Library ADR and GQ-010 records;
- final ownership of the claim/evidence operational plane;
- suitability of any source after its terms revision changes.

# Source update rule

When a source or conclusion changes:

1. preserve the old record and observed date;
2. add the new official reference or repository commit;
3. state whether the change is correction, supersession or policy update;
4. identify every dependent assertion, pilot and decision;
5. rerun the relevant rights, deletion, reproducibility and benchmark gates;
6. never update a source state solely because an agent asserts that it changed.
