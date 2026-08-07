-- Observations and projections: the replacement for one universal rank_score.
--
-- WHY THIS EXISTS
--
-- person.rank_score in the v2 schema is a single REAL column that four separate
-- loaders write incompatible quantities into:
--
--   build_people_graph_v2.py      float(work_count)        -- how many books
--   build_people_graph_v2.py      copied v1 rank_score     -- an older scheme
--   load_owners_into_people_graph.py  sum(stars)           -- GitHub popularity
--   load_owner_topics.py          += mean(overall_value)   -- a model's rating
--
-- Three defects follow, and all three are structural rather than incidental.
--
-- 1. THE COLUMN HAS NO UNIT. A value of 30910 means "summed stars" for a GitHub
--    owner and "wrote 30,910 books" for nobody at all. Comparing two rows of
--    this column compares two different measurements, so any ORDER BY over it
--    is meaningless across origins.
--
-- 2. ONE WRITER ADDS. `rank_score = COALESCE(rank_score,0) + ?` in
--    load_owner_topics.py means a second run of the same loader over the same
--    unchanged source doubles the contribution. Reruns are therefore not
--    idempotent, which is precisely what makes the build unreproducible: the
--    output depends on how many times you ran it, not on what the input said.
--
-- 3. IT CONFLATES FAME WITH VALUE. Measured in the Foundry enrichment log:
--    dtolnay, 10 repos rated >=90, 30,910 stars, ranks ABOVE facebook at
--    801,473 stars once rating is used instead of popularity. A single column
--    cannot hold both readings, and collapsing them destroys the one that is
--    actually interesting. This is an instance of the program's own diagnosed
--    category collapse: "popularity metric -> universal value".
--
-- THE FIX
--
-- Split the column into two honest layers.
--
--   person_observation  -- a NAMED, TIMESTAMPED, SOURCED measurement.
--                          "github_stars_sum for gh:dtolnay was 30910 as
--                          observed by load_owners on 2026-08-06." A fact about
--                          a measurement, which is what all four of these
--                          quantities actually are.
--
--   person_projection   -- a NAMED, VERSIONED ranking derived from observations
--                          by identified code. "rank v1 by rated value" is a
--                          different projection from "rank v1 by stars", and
--                          both may exist simultaneously without either
--                          claiming to be THE score.
--
-- Neither table is written by canonical loading. Canonical loading records what
-- a source said; ranking is a separate, rerunnable derivation. That separation
-- is what makes a rerun idempotent: an observation is REPLACED by metric+source
-- (upsert on the primary key), never accumulated.
--
-- This file is additive. It does not alter person, person_content, person_topic
-- or any other v2 table, and it does not drop person.rank_score -- removing a
-- column other lanes may still read is not this lane's call. What this lane
-- changes is that its own loaders stop writing it.

-- ---------------------------------------------------------------------------
-- person_observation : a measured quantity, with its name, time and origin.
--
-- PRIMARY KEY (person_id, metric, source) is the idempotency guarantee. Loading
-- the same metric from the same source twice REPLACES rather than accumulates,
-- so N runs of an unchanged source produce byte-identical rows. The additive
-- bug cannot be expressed in this table.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_observation (
  person_id   TEXT NOT NULL,
  metric      TEXT NOT NULL,   -- github_stars_sum | github_repo_count |
                               -- rated_overall_mean | rated_reuse_mean |
                               -- book_work_count | followers | v1_rank_score
  value       REAL NOT NULL,
  unit        TEXT NOT NULL,   -- stars | repos | rating_0_100 | works | people
                               -- The unit is REQUIRED: it is the thing whose
                               -- absence made rank_score uninterpretable.
  source      TEXT NOT NULL,   -- which loader/manifest asserted it
  snapshot    TEXT,            -- source snapshot id, ties back to the manifest
  observed_at TEXT NOT NULL,   -- when the measurement was TRUE, not when loaded
  PRIMARY KEY (person_id, metric, source)
);
CREATE INDEX IF NOT EXISTS ix_pobs_metric ON person_observation(metric, value);
CREATE INDEX IF NOT EXISTS ix_pobs_person ON person_observation(person_id);
CREATE INDEX IF NOT EXISTS ix_pobs_source ON person_observation(source);

-- observed_at means "when it was true". The Foundry enrichment log records
-- fixing exactly this semantics elsewhere in the estate: a column named
-- observed_at that actually held the load timestamp. A load timestamp belongs
-- in the build manifest, not on a fact.

-- ---------------------------------------------------------------------------
-- person_projection : a named, versioned ranking. Derived, never authoritative.
--
-- The v0 spec is explicit that "any ranking belongs to named, versioned
-- projection code with method metadata". method + method_version are therefore
-- mandatory, and the primary key includes them, so two projections coexist
-- rather than one silently overwriting the other.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS person_projection (
  person_id      TEXT NOT NULL,
  projection     TEXT NOT NULL,   -- e.g. 'rated_value', 'github_popularity'
  method         TEXT NOT NULL,   -- the rule, in words a reader can check
  method_version TEXT NOT NULL,   -- bump when the rule changes
  value          REAL NOT NULL,
  rank           INTEGER,         -- dense rank within the projection
  computed_at    TEXT NOT NULL,
  PRIMARY KEY (person_id, projection, method_version)
);
CREATE INDEX IF NOT EXISTS ix_pproj_rank ON person_projection(projection, method_version, rank);

-- ---------------------------------------------------------------------------
-- build_run : run metadata, kept OUT of canonical facts.
--
-- Spec item 7: "Separate run/build metadata from canonical facts so logical
-- reproducibility is measurable." A build timestamp stored on a person row
-- makes two otherwise-identical builds differ, which would make reproducibility
-- unmeasurable by construction. So the timestamp lives here, and the logical
-- digest deliberately excludes this table.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS build_run (
  run_id        TEXT PRIMARY KEY,
  started_at    TEXT NOT NULL,
  finished_at   TEXT,
  builder       TEXT NOT NULL,   -- which build tool + version
  schema_version TEXT NOT NULL,
  manifest_digest TEXT,          -- digest over the set of source manifests used
  notes         TEXT NOT NULL DEFAULT ''
);
