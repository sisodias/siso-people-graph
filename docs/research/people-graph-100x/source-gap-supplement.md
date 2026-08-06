# Source-gap supplement

**Cut:** 2026-08-06  
**Status:** differential research addendum; no production ingest or schema change  
**Base matrix:** `sisodias/great-library-of-siso#2` (`39` sources)  
**Base dossier:** `sisodias/siso-people-graph#6`

## Why this exists

The existing programme is already comprehensive: People Graph PR #6 preserves the broad 100x reasoning, PR #7 preserves the first-principles audit, PRs #1–#5 preserve executable safety/schema/identity/source pilots, and Great Library PR #2 preserves the primary 39-source matrix and rights/deletion analysis.

The later source-gap audit found a smaller, concrete delta. Several high-leverage sources from the latest “god-sauce” analysis were absent, represented only by a generic parent category, or needed an explicit decision boundary. This supplement records only that delta so agents do not create a third competing programme.

Machine-readable record: [`source-gap-supplement.json`](source-gap-supplement.json).

## Reconciliation rule

```text
existing 39-source matrix
  + this reviewed supplement
  -> explicit successor matrix
```

This addendum does not approve ingestion and does not silently rewrite the current source matrix.

## Missing or underrepresented sources

| Source | Gap | Why it adds value | Decision |
| --- | --- | --- | --- |
| Repository-native identity evidence | Missing source family | `CITATION.cff`, CodeMeta, `.mailmap`, maintainer files and package manifests tie explicit people/roles/ORCID/DOI to software more reliably than profile names. | Pilot first |
| DataCite + Zenodo | Missing source family | Connects software, datasets, papers, releases, creators, ORCID, ROR and related-resource DOIs. | Pilot first |
| OpenAIRE Research Graph | Missing source family | Adds projects, funders, organisations and provenance-linked research products. | Pilot after core work model |
| arXiv direct metadata | Missing direct source | Preserves preprint IDs and version history used directly by repositories, OpenReview and AI hubs. | Pilot first |
| PyVideo | Missing bounded event dataset | CC0 technical talk metadata plus an explicit `NO_PUBLISH` list makes a safe speaker/event pilot. | Pilot first |
| IETF Datatracker | Missing governance source | Adds standards documents, authors/editors, groups, meetings and dated affiliations. | Pilot first |
| Public proposal repositories | Missing governance source | PEPs, Rust RFCs, TC39 and similar repositories add champions, reviewers, states and implementation links. | Pilot first |
| public-inbox / lore | Missing discourse source | Stable Message-IDs and Git-backed threads expose patch/review relations. Privacy risk keeps it later and metadata-only. | Research later |
| World of Code | Missing research benchmark | Useful for identity split/clumping evaluation across global Git history; not canonical identity truth. | Benchmark only |
| Papers with Code historical dump | Missing historical bridge | Pinned paper↔code↔task↔dataset links complement OpenAlex/GitHub/Hugging Face. | Historical seed |
| CORDIS | Missing EU funding source | Adds EU projects and participants after measuring incremental value beyond OpenAIRE. | Research after OpenAIRE |
| SNAC | Missing historical relationship source | Links historical people, families, organisations and archival collections. | Historical phase |
| MusicBrainz | Optional scope expansion | Rich creator/work/role relations if governance expands beyond knowledge production. | Scope decision first |
| Common Crawl / Web Data Commons | Missing last-resort discovery | Targeted known-site crawling can recover `sameAs`, `rel=me` and Schema.org evidence. Broad crawl is too noisy. | Last resort |
| Semantic Scholar | Missing comparison source | May add paper/author/citation coverage, but only after measuring incremental value over OpenAlex/DBLP. | Benchmark first |
| Internet Archive item/OCR metadata | Missing payload-locator source | Adds archive/OCR locators with item-level rights and quality; metadata only by default. | Targeted only |
| Crossref Event Data | Missing attention source | Potential DOI-to-web mention/reception edges; current service state and value need recheck. | Evaluate later |
| FOSDEM + CCC archives | Specific event extension | Long-running technical speaker/session/recording metadata after source-specific rights review. | Metadata pilot |

## Highest-value correction to the first wave

The current first wave remains sound:

```text
OpenAlex + Crossref + ORCID + DBLP + ROR
GitHub + ecosyste.ms + package registries
Open Library + LOC + Wikidata
```

Add these explicitly:

```text
repository-native credit evidence
DataCite / Zenodo
direct arXiv identifiers
OpenAIRE project/funder edges
IETF and proposal-governance sources
PyVideo as the first bounded event dataset
```

## Why repository-native evidence is a separate source family

The source matrix already includes GitHub and package registries, but files inside repositories express different evidence:

```text
CITATION.cff
codemeta.json / codemeta.jsonld
.mailmap
AUTHORS
CONTRIBUTORS
MAINTAINERS
CODEOWNERS
pyproject.toml / package.json / Cargo.toml
DOI / ORCID / arXiv links
Co-authored-by trailers
```

Important semantic rules:

- owner is not creator;
- `CODEOWNERS` means review responsibility, not authorship;
- `.mailmap` is alias evidence, not permission to display email;
- repository files can be stale or copied;
- explicit ORCID/DOI/self-links create evidence-backed claims, never silent merges.

Official references:

- <https://github.com/citation-file-format/citation-file-format>
- <https://codemeta.github.io/>
- <https://codemeta.github.io/crosswalk/>

## Why DataCite/Zenodo is not covered by Crossref

Crossref is essential for scholarly DOI metadata. DataCite/Zenodo adds a different bridge population:

```text
GitHub repository
  -> CITATION.cff
  -> software/dataset DOI
  -> creator ORCID
  -> ROR affiliation
  -> related paper/project
```

Preserve concept DOI versus version DOI and never infer payload rights from public metadata.

Official references:

- <https://support.datacite.org/docs/datacite-public-data-file>
- <https://support.datacite.org/docs/datacite-data-file-use-policy>
- <https://help.zenodo.org/docs/github/enable-repository/>

## Why standards are a separate basket

IETF, PEPs, Rust RFCs, TC39 and similar systems provide typed participation and decision history:

```text
author
editor
champion
reviewer
working group
meeting
proposal state
superseded/rejected status
implementation link
```

A standards document is not merely generic content, and authorship is not community consensus.

Official repositories:

- <https://github.com/ietf-tools/datatracker>
- <https://github.com/python/peps>
- <https://github.com/rust-lang/rfcs>
- <https://github.com/tc39/proposals>

## Sources deliberately kept later

### public-inbox / lore

Useful relations, but raw email and message bodies create identity, deletion, context and privacy risk. Start only after suppression and contradiction controls, using metadata and Message-IDs rather than public display of email.

- <https://www.kernel.org/doc/projects/korg/lore.html>
- <https://www.kernel.org/lore.html>

### World of Code

Global identity maps can expose false splits and catastrophic over-merges. Use as a benchmark/candidate source only.

- <https://worldofcode.org/>
- <https://arxiv.org/abs/2607.06183>
- <https://arxiv.org/abs/2607.06920>

### Common Crawl

Use only against already-known verified personal sites. Broad `sameAs` extraction must never auto-merge identities.

- <https://commoncrawl.org/>
- <https://webdatacommons.org/>

## Scoring method

The machine ledger retains the explicit formula:

```text
3 × bridge leverage
+ 3 × identity authority
+ 2 × relationship richness
+ 2 × provenance quality
+ 2 × openness/access
+ 1 × freshness
− 2 × operational risk
```

Tier measures intrinsic leverage. Recommended phase, verification status, rights and source decision still control implementation.

## Non-claims

This supplement:

- does not approve a loader;
- does not change production data;
- does not supersede the 39-source matrix;
- does not treat draft PRs as accepted truth;
- does not permit name-only matching;
- does not authorize payload redistribution;
- does not recommend full Software Heritage, World of Code or Common Crawl ingestion;
- does not expose private chain-of-thought; it preserves reproducible evidence, alternatives, calculations, decisions and uncertainty.

## Validation

The companion JSON was checked for:

- 18 unique source IDs;
- score/tier consistency;
- HTTPS official sources;
- explicit matrix reconciliation;
- ISO checked dates;
- no credentials or private data.

Re-run:

```bash
python3 -m json.tool \
  docs/research/people-graph-100x/source-gap-supplement.json >/dev/null
```
