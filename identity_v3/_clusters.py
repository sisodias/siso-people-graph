"""Reversible decisions, deterministic clusters, redirects, and audit."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import sqlite3
from typing import Mapping, Sequence

from ._base import IdentityError, METHOD_VERSION, UnionFind, stable_id, stable_json, utc_now
from .registry import is_sentinel_value

class ClusterMixin:

    def _active_union_find(self) -> UnionFind:
        entities = [row[0] for row in self.connection.execute('SELECT entity_id FROM identity_v3_entity')]
        union = UnionFind(entities)
        for row in self.connection.execute("SELECT entity_a,entity_b FROM identity_v3_decision\n               WHERE active=1 AND outcome='accepted'"):
            union.union(row['entity_a'], row['entity_b'])
        return union

    def _component_identifier_conflicts(self, members: Sequence[str]) -> list[dict[str, object]]:
        placeholders = ','.join(('?' for _ in members))
        if not placeholders:
            return []
        grouped: dict[str, set[str]] = defaultdict(set)
        for row in self.connection.execute(f'SELECT scheme,normalized_value,uniqueness_class\n                FROM identity_v3_identifier\n                WHERE entity_id IN ({placeholders}) AND valid_to IS NULL', tuple(members)):
            if row['uniqueness_class'] == 'unique':
                grouped[row['scheme']].add(row['normalized_value'])
        return [{'scheme': scheme, 'values': sorted(values), 'members': sorted(members)} for scheme, values in sorted(grouped.items()) if len(values) > 1]

    def _prospective_members(self, a: str, b: str) -> list[str]:
        union = self._active_union_find()
        root_a, root_b = (union.find(a), union.find(b))
        members = [entity for entity in union.parent if union.find(entity) in {root_a, root_b}]
        return sorted(set(members) | {a, b})

    def _active_decision_for_candidate(self, candidate_id: str) -> sqlite3.Row | None:
        return self.connection.execute('SELECT * FROM identity_v3_decision\n               WHERE candidate_id=? AND active=1\n               ORDER BY decided_at DESC,rowid DESC LIMIT 1', (candidate_id,)).fetchone()

    def accept_candidate(self, candidate_id: str, *, decided_by: str, rationale: str='', automatic: bool=False, allow_conflicts: bool=False, decided_at: str | None=None) -> dict[str, object]:
        row = self.connection.execute('SELECT * FROM identity_v3_candidate WHERE candidate_id=?', (candidate_id,)).fetchone()
        if row is None:
            raise IdentityError(f'unknown candidate: {candidate_id}')
        active = self._active_decision_for_candidate(candidate_id)
        if active is not None:
            if active['outcome'] == 'accepted':
                return {'decision_id': active['decision_id'], 'candidate_id': candidate_id, 'generation': self.latest_generation(), 'idempotent': True}
            raise IdentityError('candidate has an active rejection; undo it before accepting')
        candidate = self._candidate_row(row)
        if automatic and (not candidate['auto_eligible']):
            raise IdentityError('candidate is review-only; automatic acceptance is forbidden')
        if automatic:
            # Defence in depth: a candidate generated before the sentinel guard
            # existed must still never auto-accept on an absence value.
            for item in candidate['positive_evidence']:
                if not isinstance(item, dict):
                    continue
                scheme, value = item.get('scheme'), item.get('value')
                if scheme and is_sentinel_value(str(scheme), str(value)):
                    raise IdentityError(
                        f'sentinel identifier {scheme}={value!r} encodes absence, '
                        'not identity; automatic acceptance is forbidden'
                    )
        if candidate['conflict_reasons'] and (not allow_conflicts):
            raise IdentityError(f"candidate has conflicts: {candidate['conflict_reasons']}")
        prospective = self._prospective_members(row['entity_a'], row['entity_b'])
        cluster_conflicts = self._component_identifier_conflicts(prospective)
        if cluster_conflicts and (not allow_conflicts):
            raise IdentityError(f'acceptance would create conflicting stable identifiers: {cluster_conflicts}')
        when = decided_at or utc_now()
        decision_id = stable_id('decision', candidate_id, 'accepted', decided_by, when)
        self.connection.execute('INSERT INTO identity_v3_decision\n               (decision_id,candidate_id,entity_a,entity_b,outcome,active,\n                decided_by,decided_at,rationale)\n               VALUES (?,?,?,?,? ,1,?,?,?)', (decision_id, candidate_id, row['entity_a'], row['entity_b'], 'accepted', decided_by, when, rationale))
        self.connection.execute("UPDATE identity_v3_candidate SET review_state='accepted',updated_at=? WHERE candidate_id=?", (when, candidate_id))
        generation = self.recompute_clusters(reason=f'accept:{decision_id}', created_at=when)
        self.connection.commit()
        return {'decision_id': decision_id, 'candidate_id': candidate_id, 'generation': generation}

    def reject_candidate(self, candidate_id: str, *, decided_by: str, rationale: str='', decided_at: str | None=None) -> dict[str, object]:
        row = self.connection.execute('SELECT * FROM identity_v3_candidate WHERE candidate_id=?', (candidate_id,)).fetchone()
        if row is None:
            raise IdentityError(f'unknown candidate: {candidate_id}')
        active = self._active_decision_for_candidate(candidate_id)
        if active is not None:
            if active['outcome'] == 'rejected':
                return {'decision_id': active['decision_id'], 'candidate_id': candidate_id, 'idempotent': True}
            raise IdentityError('candidate has an active acceptance; undo it before rejecting')
        when = decided_at or utc_now()
        decision_id = stable_id('decision', candidate_id, 'rejected', decided_by, when)
        self.connection.execute('INSERT INTO identity_v3_decision\n               (decision_id,candidate_id,entity_a,entity_b,outcome,active,\n                decided_by,decided_at,rationale)\n               VALUES (?,?,?,?,?,1,?,?,?)', (decision_id, candidate_id, row['entity_a'], row['entity_b'], 'rejected', decided_by, when, rationale))
        self.connection.execute("UPDATE identity_v3_candidate SET review_state='rejected',updated_at=? WHERE candidate_id=?", (when, candidate_id))
        self.connection.commit()
        return {'decision_id': decision_id, 'candidate_id': candidate_id}

    def undo_decision(self, decision_id: str | None=None, *, reverted_at: str | None=None) -> dict[str, object]:
        if decision_id:
            row = self.connection.execute('SELECT * FROM identity_v3_decision WHERE decision_id=? AND active=1', (decision_id,)).fetchone()
        else:
            row = self.connection.execute('SELECT * FROM identity_v3_decision WHERE active=1\n                   ORDER BY decided_at DESC, rowid DESC LIMIT 1').fetchone()
        if row is None:
            raise IdentityError('no active decision to undo')
        when = reverted_at or utc_now()
        self.connection.execute('UPDATE identity_v3_decision SET active=0,reverted_at=? WHERE decision_id=?', (when, row['decision_id']))
        remaining = self.connection.execute('SELECT outcome FROM identity_v3_decision\n               WHERE candidate_id=? AND active=1\n               ORDER BY decided_at DESC,rowid DESC LIMIT 1', (row['candidate_id'],)).fetchone()
        state = remaining['outcome'] if remaining else 'proposed'
        self.connection.execute('UPDATE identity_v3_candidate SET review_state=?,updated_at=? WHERE candidate_id=?', (state, when, row['candidate_id']))
        generation = self.recompute_clusters(reason=f"undo:{row['decision_id']}", created_at=when)
        self.connection.commit()
        return {'undone_decision_id': row['decision_id'], 'candidate_id': row['candidate_id'], 'generation': generation}

    def _canonical_sort_key(self, entity_id: str, metadata: Mapping[str, sqlite3.Row]) -> tuple[object, ...]:
        meta = metadata[entity_id]
        origin_priority = {'registry': 0, 'curated': 0, 'manual': 0, 'authority': 1, 'book': 2, 'books': 2, 'github': 3, 'youtube': 3}
        strong_count = self.connection.execute('SELECT COUNT(*) FROM identity_v3_identifier\n               WHERE entity_id=? AND auto_resolution_eligible=1 AND valid_to IS NULL', (entity_id,)).fetchone()[0]
        return (origin_priority.get((meta['origin'] or '').casefold(), 9), -int(strong_count), entity_id)

    def recompute_clusters(self, *, reason: str, created_at: str | None=None) -> int:
        union = self._active_union_find()
        metadata = self._entity_metadata()
        decisions = [tuple(row) for row in self.connection.execute("SELECT decision_id,candidate_id,entity_a,entity_b,outcome\n               FROM identity_v3_decision WHERE active=1 AND outcome='accepted'\n               ORDER BY decision_id")]
        digest = hashlib.sha256(stable_json(decisions).encode('utf-8')).hexdigest()
        when = created_at or utc_now()
        cursor = self.connection.execute('INSERT INTO identity_v3_generation(reason,decision_digest,created_at) VALUES (?,?,?)', (reason, digest, when))
        generation = int(cursor.lastrowid)
        for members in union.components():
            canonical = min(members, key=lambda entity: self._canonical_sort_key(entity, metadata))
            cluster_id = stable_id('cluster', sorted(members), length=20)
            self.connection.executemany('INSERT INTO identity_v3_cluster_member\n                   (generation,entity_id,cluster_id,canonical_entity_id)\n                   VALUES (?,?,?,?)', [(generation, entity, cluster_id, canonical) for entity in members])
        return generation

    def latest_generation(self) -> int | None:
        row = self.connection.execute('SELECT MAX(generation) FROM identity_v3_generation').fetchone()
        return int(row[0]) if row and row[0] is not None else None

    def resolve_entity(self, entity_id: str) -> dict[str, object]:
        generation = self.latest_generation()
        if generation is None:
            generation = self.recompute_clusters(reason='initial')
            self.connection.commit()
        row = self.connection.execute('SELECT * FROM identity_v3_cluster_member\n               WHERE generation=? AND entity_id=?', (generation, entity_id)).fetchone()
        if row is None:
            raise IdentityError(f'unknown entity: {entity_id}')
        members = [member[0] for member in self.connection.execute('SELECT entity_id FROM identity_v3_cluster_member\n               WHERE generation=? AND cluster_id=? ORDER BY entity_id', (generation, row['cluster_id']))]
        return {'entity_id': entity_id, 'canonical_entity_id': row['canonical_entity_id'], 'redirected': entity_id != row['canonical_entity_id'], 'cluster_id': row['cluster_id'], 'generation': generation, 'members': members}

    def inspect_entity(self, entity_id: str) -> dict[str, object]:
        entity = self.connection.execute('SELECT * FROM identity_v3_entity WHERE entity_id=?', (entity_id,)).fetchone()
        if entity is None:
            raise IdentityError(f'unknown entity: {entity_id}')
        identifiers = [dict(row) for row in self.connection.execute('SELECT scheme,value,scope,uniqueness_class,mutability,authority,\n                      auto_resolution_eligible,source,valid_from,valid_to,observed_at\n               FROM identity_v3_identifier WHERE entity_id=? ORDER BY scheme,value', (entity_id,))]
        aliases = [dict(row) for row in self.connection.execute('SELECT scheme,alias,valid_from,valid_to,source,\n                      stable_identifier_scheme,stable_identifier_value,observed_at\n               FROM identity_v3_alias WHERE entity_id=? ORDER BY scheme,valid_from,alias', (entity_id,))]
        attributes = [{**dict(row), 'value': json.loads(row['value_json'])} for row in self.connection.execute('SELECT source,attribute,value_json,observed_at,payload_sha256\n                   FROM identity_v3_attribute WHERE entity_id=?\n                   ORDER BY observed_at,source,attribute', (entity_id,))]
        candidates = [self._candidate_row(row) for row in self.connection.execute('SELECT * FROM identity_v3_candidate\n               WHERE entity_a=? OR entity_b=? ORDER BY confidence DESC', (entity_id, entity_id))]
        return {'entity': dict(entity), 'identifiers': identifiers, 'aliases': aliases, 'attributes': attributes, 'candidates': candidates, 'resolution': self.resolve_entity(entity_id)}

    def audit(self) -> dict[str, object]:
        generation = self.latest_generation()
        if generation is None:
            generation = self.recompute_clusters(reason='audit')
            self.connection.commit()
        clusters: dict[str, list[str]] = defaultdict(list)
        for row in self.connection.execute('SELECT cluster_id,entity_id FROM identity_v3_cluster_member\n               WHERE generation=? ORDER BY cluster_id,entity_id', (generation,)):
            clusters[row['cluster_id']].append(row['entity_id'])
        cluster_conflicts: list[dict[str, object]] = []
        for cluster_id, members in clusters.items():
            conflicts = self._component_identifier_conflicts(members)
            if conflicts:
                cluster_conflicts.append({'cluster_id': cluster_id, 'members': members, 'conflicts': conflicts})
        unsafe = []
        for row in self.connection.execute("SELECT candidate_id,method,conflict_reasons_json,review_state\n               FROM identity_v3_candidate\n               WHERE conflict_reasons_json!='[]'"):
            unsafe.append({'candidate_id': row['candidate_id'], 'method': row['method'], 'review_state': row['review_state'], 'conflicts': json.loads(row['conflict_reasons_json'])})
        counts = {'entities': self.connection.execute('SELECT COUNT(*) FROM identity_v3_entity').fetchone()[0], 'identifiers': self.connection.execute('SELECT COUNT(*) FROM identity_v3_identifier').fetchone()[0], 'aliases': self.connection.execute('SELECT COUNT(*) FROM identity_v3_alias').fetchone()[0], 'attributes': self.connection.execute('SELECT COUNT(*) FROM identity_v3_attribute').fetchone()[0], 'candidates': self.connection.execute('SELECT COUNT(*) FROM identity_v3_candidate').fetchone()[0], 'active_acceptances': self.connection.execute("SELECT COUNT(*) FROM identity_v3_decision WHERE active=1 AND outcome='accepted'").fetchone()[0], 'clusters': len(clusters)}
        return {'method_version': METHOD_VERSION, 'generation': generation, 'counts': counts, 'cluster_conflicts': cluster_conflicts, 'unsafe_candidates': unsafe, 'invariants_ok': not cluster_conflicts}
