-- Foundry — People graph, v2
--
-- v1 was designed for GitHub + YouTube: 471 people, 3 domains, a leaderboard of
-- 140 tiered humans. It worked. Then books landed 35,363 more people and 72,137
-- edges in one merge, and three design assumptions broke in ways worth fixing
-- before Twitter, Reddit and the rest arrive.
--
-- MEMBERSHIP RULE (Shaan, 2026-08-03): the graph holds PEOPLE WHO PRODUCED
-- SOMETHING. A book author is a first-class member alongside a repo owner or a
-- channel creator. Overlaps -- an author who also ships code and posts -- are
-- the high-value multi-source cases the graph exists to surface.
--
-- WHAT v1 GOT RIGHT (kept verbatim in spirit):
--   * one canonical entity + thin external_ids + generic content edges
--   * satellites are REFERENCED, never duplicated
--   * namespaced stable ids ('gh:', 'yt:', now 'bk:')
--
-- WHAT BROKE, and why each change below exists:
--
-- 1. IDENTITY MATCHING WAS IMPLICIT AND UNSAFE.
--    The books merge matched 223 people by normalised name alone. It happened to
--    produce zero collisions -- verified -- but that is luck, not design. Two
--    different humans named "John Murray" would silently become one person and
--    the graph would assert something false. At 36k people the birthday problem
--    is already against us; at a million it is certain.
--    -> identity_claim: every match is an explicit, evidenced, reversible row.
--       Nothing silently merges. A claim carries its method and confidence, and
--       a wrong claim is deleted without touching the underlying people.
--
-- 2. EDGES CARRIED NO PROVENANCE.
--    person_content had (person_id, domain, content_ref, score, title, meta_json)
--    -- no record of WHERE the edge came from or WHEN. When an edge is wrong you
--    cannot tell which loader wrote it or whether a re-run would recreate it.
--    -> every edge now carries source + observed_at, so a bad loader's output is
--       identifiable and removable as a set.
--
-- 3. layer_count HARDCODED THE DOMAIN LIST.
--    v_person_layers enumerated youtube/github/registry in a CASE expression, so
--    the books domain scored layers=0 for 35,363 people until the view was
--    rewritten by hand. Every new domain silently under-reports until someone
--    notices.
--    -> the view now counts DISTINCT domain generically. New domains work with
--       no edit.
--
-- 4. 'role' SAT ON THE PERSON, NOT THE EDGE.
--    A person is not globally "an author" -- they authored THIS work and
--    translated THAT one. Books proved the cost: flattening roles would have made
--    a Gutenberg volunteer editor the second most prolific author in history.
--    -> role moves to the edge, where it belongs.
--
-- 5. NO WAY TO SAY "TRACKED BUT NOTHING LINKED YET".
--    9,395 registry people (Andrew Ng, Jim Keller) have zero content edges. They
--    are not errors -- they are people we care about whose output is not yet
--    mapped. v1 could not express that, so they looked identical to broken rows.
--    -> person.state makes the distinction explicit and queryable.
--
-- Single-writer law unchanged: this DB lives on the vault, written by one
-- process; everyone else opens it with ?mode=ro via core/db.py connect_ro().

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- person : the canonical entity. ONE ROW PER HUMAN (or organisation).
-- person_id stays namespaced and stable: 'gh:<login>', 'yt:<slug>',
-- 'bk:<key>', or a registry slug for hand-curated people.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person (
  person_id     TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  sort_name     TEXT,                       -- surname-first, for ordering
  kind          TEXT NOT NULL DEFAULT 'human'
                  CHECK (kind IN ('human','organisation','pseudonym','unknown')),
  -- Books flags 870 "authors" that are institutions ("United States", "Various").
  -- They are real catalog entities but they are not people; conflating them
  -- corrupts any question of the form "what does this person believe".

  state         TEXT NOT NULL DEFAULT 'linked'
                  CHECK (state IN ('tracked','linked','merged','disputed')),
  -- tracked  = we care, nothing linked yet (the 9,395 registry case)
  -- linked   = has at least one content edge
  -- merged   = superseded by another person_id (see merged_into)
  -- disputed = an identity_claim on this person failed review

  merged_into   TEXT REFERENCES person(person_id) ON DELETE SET NULL,
  -- Merges are NON-DESTRUCTIVE. The losing row survives pointing at the winner,
  -- so a bad merge is one UPDATE to undo. v1 had no reversal path at all.

  birth_year    INTEGER,                    -- negative = BCE. Plato = -428.
  death_year    INTEGER,
  primary_tier  TEXT,                       -- S/A/B/C where curated
  rank_score    REAL,
  origin        TEXT NOT NULL,              -- domain where FIRST materialised
  topics_json   TEXT NOT NULL DEFAULT '[]',
  built_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_person_name   ON person(name);
CREATE INDEX IF NOT EXISTS ix_person_sort   ON person(sort_name);
CREATE INDEX IF NOT EXISTS ix_person_state  ON person(state);
CREATE INDEX IF NOT EXISTS ix_person_kind   ON person(kind);
CREATE INDEX IF NOT EXISTS ix_person_birth  ON person(birth_year);
CREATE INDEX IF NOT EXISTS ix_person_origin ON person(origin);

-- ---------------------------------------------------------------------------
-- external_ids : platform identities. The join key across domains.
-- Unchanged from v1 except that value is indexed for reverse lookup, which is
-- how the matcher will find "does this github login already exist".
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS external_ids (
  person_id  TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  platform   TEXT NOT NULL,   -- github_login | youtube_channel_id | x_handle |
                              -- reddit_user | website | viaf | wikidata | isni
  value      TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  source     TEXT,            -- which loader asserted this
  PRIMARY KEY (person_id, platform, value)
);
CREATE INDEX IF NOT EXISTS ix_extid_lookup ON external_ids(platform, value);

-- Authority identifiers (VIAF, Wikidata, ISNI) are listed deliberately: they are
-- the only way to resolve historical people correctly. "Plato" as a string is
-- ambiguous; VIAF 108159964 is not. Populating these is how cross-domain stitch
-- gets past its current count of 3.

-- ---------------------------------------------------------------------------
-- content : the edge. person -> a unit of output in some domain.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_content (
  person_id   TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  domain      TEXT NOT NULL,   -- github | youtube_video | youtube_channel |
                               -- book | x_post | reddit_post | podcast
  content_ref TEXT NOT NULL,   -- repo full_name | video_id | gutenberg gid | ...
  role        TEXT NOT NULL DEFAULT 'author',
  -- ON THE EDGE, not the person: author | editor | translator | illustrator |
  -- commentator | owner | contributor | host | guest. Books captured a dozen.

  score       REAL,
  title       TEXT,
  source      TEXT NOT NULL DEFAULT 'unknown',  -- which loader wrote this row
  observed_at TEXT,                              -- when it was true
  meta_json   TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (person_id, domain, content_ref, role)
);
CREATE INDEX IF NOT EXISTS ix_pc_person ON person_content(person_id);
CREATE INDEX IF NOT EXISTS ix_pc_domain ON person_content(domain);
CREATE INDEX IF NOT EXISTS ix_pc_ref    ON person_content(domain, content_ref);
CREATE INDEX IF NOT EXISTS ix_pc_source ON person_content(source);

-- ---------------------------------------------------------------------------
-- identity_claim : the thing v1 was missing entirely.
-- An assertion that two person rows are the same human. Evidenced, scored, and
-- reversible. The matcher writes claims; a human or a gate promotes them.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS identity_claim (
  claim_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  person_a    TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  person_b    TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  method      TEXT NOT NULL,   -- exact_name | name_plus_years | shared_external_id
                               -- | authority_file | manual
  confidence  REAL NOT NULL,
  evidence    TEXT NOT NULL,   -- the actual matched values, so a human can check
  status      TEXT NOT NULL DEFAULT 'proposed'
                CHECK (status IN ('proposed','accepted','rejected')),
  decided_by  TEXT,
  created_at  TEXT NOT NULL,
  CHECK (person_a < person_b)  -- canonical ordering; one claim per pair
);
CREATE INDEX IF NOT EXISTS ix_claim_status ON identity_claim(status);
CREATE INDEX IF NOT EXISTS ix_claim_a ON identity_claim(person_a);
CREATE INDEX IF NOT EXISTS ix_claim_b ON identity_claim(person_b);

-- Name-only matching is recorded as method='exact_name' with LOW confidence on
-- purpose. It is a hypothesis, not a merge. Only shared_external_id and
-- authority_file justify auto-acceptance.

-- ---------------------------------------------------------------------------
-- person_topic : what a person is ABOUT, as a joinable edge.
--
-- v1 had topics_json -- free text, unqueryable, unjoinable. But the books domain
-- already carries 184,624 work->subject edges under Library of Congress subject
-- headings, assigned by librarians. A person's topics are derivable from the
-- subjects of what they produced, and once they are rows you can ask "who else
-- wrote about this", which free text cannot answer.
--
-- weight = how much of their output sits under this topic, so a person who wrote
-- forty books on ethics ranks above one who mentioned it once.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_topic (
  person_id TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  topic     TEXT NOT NULL,   -- LCSH heading, LoC class, or curated tag
  scheme    TEXT NOT NULL DEFAULT 'lcsh',  -- lcsh | locc | curated | derived
  weight    REAL NOT NULL DEFAULT 1.0,
  source    TEXT,
  PRIMARY KEY (person_id, topic, scheme)
);
CREATE INDEX IF NOT EXISTS ix_ptopic_topic ON person_topic(topic, scheme);

-- ===========================================================================
-- RECOVERED SCHEMA: the four tables that shipped without ever being tracked.
--
-- These are not new. They exist in the published graph-v2 release asset
-- (people_graph_v2.sqlite, sha256 9938237a3327...) and held 1,287,159 rows
-- there, yet appeared in NO tracked file on ANY branch of this repository.
-- The DDL below is recovered verbatim from that asset's sqlite_master, so the
-- tracked schema now describes the graph that actually shipped.
--
-- Why this block exists rather than a quiet CREATE TABLE: a table that lives in
-- production and in no schema is precisely how a graph becomes unrebuildable.
-- Recording the recovery, and the semantics, is the point.
-- See docs/handoffs/schema-divergence.md for when and how this happened.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- organisation : companies, projects and foundations, kept OUT of person.
--
-- The design reason is the one the README defends: conflating an institution
-- with a human corrupts any question of the form "what does this person
-- believe". 1,131 rows shipped.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS organisation (
  org_id        TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  kind          TEXT NOT NULL DEFAULT 'unknown'
                  CHECK (kind IN ('company','project','foundation','team','unknown')),
  github_org_id TEXT,
  state         TEXT NOT NULL DEFAULT 'tracked'
                  CHECK (state IN ('tracked','linked','merged','disputed')),
  source        TEXT NOT NULL,
  observed_at   TEXT,
  meta_json     TEXT NOT NULL DEFAULT '{}'
);

-- ---------------------------------------------------------------------------
-- person_organisation : membership. Shipped EMPTY (0 rows) -- the table was
-- created but nothing ever populated it, so "who works where" is currently
-- unanswerable. Tracked so that stays visible rather than being rediscovered.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_organisation (
  person_id   TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  org_id      TEXT NOT NULL REFERENCES organisation(org_id) ON DELETE CASCADE,
  relation    TEXT NOT NULL,
  started_at  TEXT,
  ended_at    TEXT,
  confidence  REAL NOT NULL DEFAULT 0.9,
  source      TEXT NOT NULL,
  observed_at TEXT,
  meta_json   TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (person_id, org_id, relation)
);

-- ---------------------------------------------------------------------------
-- organisation_content : what an organisation produced. 13,533 rows shipped,
-- every one from crates_io_teams.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS organisation_content (
  org_id      TEXT NOT NULL REFERENCES organisation(org_id) ON DELETE CASCADE,
  domain      TEXT NOT NULL,
  content_ref TEXT NOT NULL,
  role        TEXT,
  source      TEXT NOT NULL,
  observed_at TEXT,
  meta_json   TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (org_id, domain, content_ref, role)
);

-- ---------------------------------------------------------------------------
-- person_person : edges between people. READ THE SEMANTICS BEFORE USING THIS.
--
-- 1,272,495 rows shipped, and the release title calls them "person-to-person
-- edges". They are not social edges. Measured against the asset:
--
--     relation   = 'depends_on'                     (1,272,495 of 1,272,495)
--     source     = 'crates_io_dependencies'         (1,272,495 of 1,272,495)
--     confidence = 0.95 flat                        (min = max = 0.95)
--
-- Every row is a crates.io PACKAGE DEPENDENCY projected onto package owners.
-- Package A depends on package B does not mean person A knows, has worked
-- with, or has any relationship to person B. The flat confidence carries no
-- discriminating information: it cannot rank, filter or separate anything.
--
-- This table therefore does NOT support "who knows whom", collaboration
-- inference, or any social-graph feature. It supports exactly one honest
-- question: whose packages sit upstream of whose. Anything more is the
-- owner -> creator category collapse the consolidation plan names.
--
-- The column is `relation` precisely so a future genuine relation (co_author,
-- co_maintainer) can coexist without inheriting this one's meaning. Filter on
-- relation and source; never treat the table as homogeneous.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_person (
  person_a    TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  person_b    TEXT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
  relation    TEXT NOT NULL,
  direction   TEXT NOT NULL DEFAULT 'a_to_b',
  weight      INTEGER NOT NULL DEFAULT 1,
  confidence  REAL NOT NULL DEFAULT 0.9,
  source      TEXT NOT NULL,
  observed_at TEXT,
  meta_json   TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (person_a, person_b, relation),
  CHECK (person_a <> person_b)
);
CREATE INDEX IF NOT EXISTS ix_pperson_b ON person_person(person_b, relation);

-- ---------------------------------------------------------------------------
-- person_search : FTS over names.
--
-- Finding "Nietzsche" by LIKE '%...%' is a full table scan -- measured 57ms at
-- 36k people, and it grows linearly. At a million it is unusable, and name
-- lookup is the single most common entry point into the graph.
-- Populated by the builder; rebuilt, never hand-edited.
-- ---------------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS person_search USING fts5(
  person_id UNINDEXED,
  name,
  aliases,          -- every raw variant that mapped to this person
  tokenize = 'unicode61 remove_diacritics 2'
);
-- remove_diacritics matters: "Honoré de Balzac" must be findable as "Balzac".

-- ---------------------------------------------------------------------------
-- v_person_layers : cross-domain reach. Generic over domains -- adding a new
-- one needs no edit here, which is the bug this replaces.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_person_layers;
CREATE VIEW v_person_layers AS
SELECT
  p.person_id,
  p.name,
  p.kind,
  p.state,
  p.primary_tier,
  p.origin,
  COUNT(DISTINCT CASE WHEN c.domain LIKE 'youtube%' THEN 'youtube'
                      ELSE c.domain END)            AS domain_count,
  COUNT(c.content_ref)                              AS content_count,
  GROUP_CONCAT(DISTINCT CASE WHEN c.domain LIKE 'youtube%' THEN 'youtube'
                             ELSE c.domain END)     AS domains
FROM person p
LEFT JOIN person_content c ON c.person_id = p.person_id
WHERE p.state != 'merged'
GROUP BY p.person_id;

-- The multi-source people are the point of the whole graph: someone with a repo,
-- a talk and a book is a position you can triangulate. Query:
--   SELECT * FROM v_person_layers WHERE domain_count >= 2 ORDER BY content_count DESC;

-- ---------------------------------------------------------------------------
-- v_contemporaries : people whose lives overlapped.
--
-- Intellectual history is largely a conversation between people who were alive
-- at the same time. Spinoza (1632-1677) and Locke (1632-1704) were reacting to
-- the same world; Spinoza and Nietzsche were not. This view makes that a join
-- rather than a manual lookup, and it only works because birth/death are real
-- columns with BCE stored negative -- so antiquity participates instead of
-- silently dropping out.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_contemporaries;
CREATE VIEW v_contemporaries AS
SELECT
  a.person_id   AS person_id,
  a.name        AS name,
  b.person_id   AS contemporary_id,
  b.name        AS contemporary_name,
  MAX(a.birth_year, b.birth_year) AS overlap_start,
  MIN(COALESCE(a.death_year, a.birth_year + 80),
      COALESCE(b.death_year, b.birth_year + 80)) AS overlap_end
FROM person a
JOIN person b
  ON a.person_id <> b.person_id
 AND a.birth_year IS NOT NULL
 AND b.birth_year IS NOT NULL
 AND MAX(a.birth_year, b.birth_year)
     < MIN(COALESCE(a.death_year, a.birth_year + 80),
           COALESCE(b.death_year, b.birth_year + 80))
WHERE a.state != 'merged' AND b.state != 'merged';

-- COALESCE(death, birth+80) handles people whose death year the catalog omits.
-- It is an assumption, deliberately visible here rather than hidden in a loader.
