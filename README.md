# SISO People Graph

One canonical graph of **people who produced something** — books, code, video —
with their work, their topics, and when they lived.

**280,708 people · 564,486 works · 2,050,629 topic edges · 253,815 platform identities**

## Why this exists

Domains scrape *content*. But content is made by *people*, and the same human
appears as a GitHub login, a YouTube channel, an author name on a book. The
people graph is the layer where "everything this human ever produced" becomes a
single query instead of four.

The membership rule is deliberately simple: **you are in the graph if you
produced something.** A book author is a first-class member alongside a repo
owner. Overlaps — someone who ships code *and* writes *and* speaks — are the
high-value cases the graph exists to surface.

## What's in it

| | |
| --- | --- |
| people | 280,708 (37,647 confirmed human, 7,329 organisations) |
| with life dates | 27,583 — BCE stored negative, so Plato is −428 |
| content edges | github 463,230 · book 101,124 · youtube 132 |
| topic edges | 2,050,629 across five separate vocabularies |
| platform identities | 253,815 |

Topic vocabularies are kept **separate, never merged**: `github_topic`
(1,206,260), `gh_category` (309,716), `github_lang` (287,516), `lcsh` (167,585),
`curated` (53,072). "python" and "Philosophy, Ancient" are not the same kind of
fact, and flattening them would make both untrustworthy.

## Queries it answers

```sql
-- Everything one person produced, any medium
SELECT domain, title, role FROM person_content WHERE person_id = 'plato';
-- 71 works: Apology, The Republic, Critias, Timaeus, Lysis, Charmides…

-- Who overlapped with Spinoza, filtered to philosophers
SELECT contemporary_name, overlap_start, overlap_end FROM v_contemporaries
WHERE person_id = (SELECT person_id FROM person WHERE name LIKE 'Spinoza%');
-- Descartes, Hobbes, Leibniz — the actual 17th-century conversation

-- Multi-source people: a repo AND a talk AND a book is a position you can triangulate
SELECT * FROM v_person_layers WHERE domain_count >= 2 ORDER BY content_count DESC;
```

## Design decisions, and what forced them

**Roles live on the edge, not the person.** Someone authored *this* and
translated *that*. Flattening roles would make a Gutenberg volunteer editor the
second most prolific author in history — that is a real record in this data, not
a hypothetical.

**Identity claims, never silent merges.** Matching on names is unsafe at scale:
two humans named "John Murray" would fuse into one and the graph would assert
something false forever. Every proposed match is a row in `identity_claim` with
a method, a confidence and the literal evidence, so a wrong claim costs one
DELETE rather than a corrupted entity table. Methods ranked by trust:
`shared_external_id` (0.98) → `name_plus_years` (0.90) → `exact_name` (0.55) →
`surname_initial` (0.45).

**Merges are reversible.** `merged_into` points a losing row at the winner
rather than deleting it. A bad merge is one UPDATE to undo.

**Nothing derived is stored.** No stamped score, no independent tier. In a
sibling system, storing tier alongside score produced a **96.6% contradiction
rate** — 4,995 pages labelled top-tier while carrying bottom-tier scores. Derive
or don't claim.

**`state` distinguishes tracked from broken.** 9,395 curated people have no
content edges yet. They are not errors; they are people whose output is not
mapped. A schema that cannot say that makes them look like corruption.

**BCE years are negative.** Without it, every ancient author parses with null
dates and any century filter silently drops the entire classical corpus.

## The honest limitation

**Cross-domain stitch is 3.** Not 3%, three people — Karpathy, Jensen Huang,
Simon Willison, all GitHub + YouTube.

Not a bug, and not fixable by better matching. Measured: **20,246 book people
died before 1950; only 334 are alive after 2000.** Gutenberg is a public-domain
corpus, so its people are mostly dead, and GitHub's are alive. There is no
Spinoza with a GitHub account to find. The theoretical maximum overlap is ~419
people, not thousands.

An earlier assumption — that resolving GitHub logins to real names would unlock
mass stitching — was tested and is **false**. `real_name` from the GitHub API is
frequently a project name, not a person's: `.NET Core Community`, `37signals`,
`AFNetworking`. The enrichment is still worth running, for the human/organisation
split and topic signal, but not as a stitch fix.

The populations that *should* overlap are living writers, modern technical
authors, and podcast guests — sources not yet loaded.

## Build it

```bash
python3 loaders/build_people_graph_books.py --books books.sqlite --db people.sqlite
python3 loaders/build_people_graph_v2.py --v1 canonical.sqlite --people people.sqlite \
    --books books.sqlite --out people_v2.sqlite
python3 loaders/load_owners_into_people_graph.py --identity identity.sqlite \
    --graph people_v2.sqlite --min-stars 100 --apply
python3 loaders/load_owner_topics.py --identity identity.sqlite --graph people_v2.sqlite --apply
python3 loaders/enrich_owners.py --graph people_v2.sqlite --limit 4000
```

`loaders/ask.py` is the query surface — an agent with a question does not need to
know which database holds the answer.

## Part of

The [SISO Foundry](https://github.com/sisodias/siso-foundry) — one
domain-agnostic engine: scrape the content, scrape the people who make it, watch
them over time, then research over the result. Books come from the
[SISO Book Library](https://github.com/sisodias/siso-book-library).
