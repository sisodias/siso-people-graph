"""Candidate generation and review queue for identity_v3."""
from __future__ import annotations

from collections import defaultdict
import json
import sqlite3
from typing import Mapping

from ._base import METHOD_VERSION, stable_id, stable_json, utc_now
from .registry import is_auto_resolvable, is_sentinel_value, name_parts, normalize_name, rule_for, years_compatible

class CandidateMixin:

    def _entity_metadata(self) -> dict[str, sqlite3.Row]:
        rows = self.connection.execute('SELECT * FROM identity_v3_entity').fetchall()
        return {row['entity_id']: row for row in rows}

    def _identifiers_by_entity(self) -> dict[str, dict[str, set[str]]]:
        result: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for row in self.connection.execute('SELECT entity_id,scheme,normalized_value FROM identity_v3_identifier WHERE valid_to IS NULL'):
            result[row['entity_id']][row['scheme']].add(row['normalized_value'])
        return result

    def _pair_conflicts(self, entity_a: str, entity_b: str, metadata: Mapping[str, sqlite3.Row], identifiers: Mapping[str, Mapping[str, set[str]]]) -> tuple[list[dict[str, object]], list[str]]:
        negative: list[dict[str, object]] = []
        conflicts: list[str] = []
        meta_a, meta_b = (metadata[entity_a], metadata[entity_b])
        kind_a, kind_b = (meta_a['kind'], meta_b['kind'])
        if {kind_a, kind_b} == {'human', 'organisation'}:
            negative.append({'type': 'kind_conflict', 'a': kind_a, 'b': kind_b})
            conflicts.append('human_organisation_conflict')
        if not years_compatible((meta_a['birth_year'], meta_a['death_year']), (meta_b['birth_year'], meta_b['death_year'])):
            negative.append({'type': 'life_date_conflict', 'a': [meta_a['birth_year'], meta_a['death_year']], 'b': [meta_b['birth_year'], meta_b['death_year']]})
            conflicts.append('life_date_conflict')
        schemes = set(identifiers.get(entity_a, {})) & set(identifiers.get(entity_b, {}))
        for scheme in sorted(schemes):
            rule = rule_for(scheme)
            if rule.uniqueness != 'unique':
                continue
            values_a = identifiers[entity_a][scheme]
            values_b = identifiers[entity_b][scheme]
            if values_a and values_b and values_a.isdisjoint(values_b):
                negative.append({'type': 'conflicting_unique_identifier', 'scheme': scheme, 'a': sorted(values_a), 'b': sorted(values_b)})
                conflicts.append(f'conflicting_{scheme}')
        return (negative, conflicts)

    def generate_candidates(self, *, apply: bool=True) -> list[dict[str, object]]:
        metadata = self._entity_metadata()
        identifiers = self._identifiers_by_entity()
        pair_signals: dict[tuple[str, str], dict[str, object]] = {}

        def pair(a: str, b: str) -> tuple[str, str]:
            return (a, b) if a < b else (b, a)

        def add_signal(a: str, b: str, *, method: str, confidence: float, priority: int, auto_eligible: bool, positive: Mapping[str, object]) -> None:
            if a == b:
                return
            key = pair(a, b)
            rec = pair_signals.setdefault(key, {'priority': -1, 'method': method, 'confidence': confidence, 'auto_eligible': auto_eligible, 'positive': []})
            rec['positive'].append(dict(positive))
            if priority > int(rec['priority']):
                rec['priority'] = priority
                rec['method'] = method
                rec['confidence'] = confidence
                rec['auto_eligible'] = auto_eligible
            elif method == rec['method']:
                rec['confidence'] = max(float(rec['confidence']), confidence)
                rec['auto_eligible'] = bool(rec['auto_eligible']) or auto_eligible
        by_identifier: dict[tuple[str, str], list[str]] = defaultdict(list)
        for entity_id, schemes in identifiers.items():
            for scheme, values in schemes.items():
                if not is_auto_resolvable(scheme):
                    continue
                for value in values:
                    # A sentinel encodes "no account", so every row carrying it
                    # would otherwise appear to share one unique identifier.
                    if is_sentinel_value(scheme, value):
                        continue
                    by_identifier[scheme, value].append(entity_id)
        for (scheme, value), entities in sorted(by_identifier.items()):
            unique_entities = sorted(set(entities))
            for index, a in enumerate(unique_entities):
                for b in unique_entities[index + 1:]:
                    add_signal(a, b, method='shared_external_id', confidence=0.995, priority=400, auto_eligible=True, positive={'type': 'eligible_identifier_match', 'scheme': scheme, 'value': value, 'method_version': METHOD_VERSION})
        by_name: dict[str, list[str]] = defaultdict(list)
        by_surname: dict[tuple[str, str], list[str]] = defaultdict(list)
        for entity_id, meta in metadata.items():
            normalized = normalize_name(meta['label'])
            if normalized:
                by_name[normalized].append(entity_id)
            surname, given = name_parts(meta['label'])
            if surname:
                by_surname[surname, given[:1]].append(entity_id)
        for normalized, entities in sorted(by_name.items()):
            unique_entities = sorted(set(entities))
            for index, a in enumerate(unique_entities):
                for b in unique_entities[index + 1:]:
                    meta_a, meta_b = (metadata[a], metadata[b])
                    compatible = years_compatible((meta_a['birth_year'], meta_a['death_year']), (meta_b['birth_year'], meta_b['death_year']))
                    both_dated = (meta_a['birth_year'] is not None or meta_a['death_year'] is not None) and (meta_b['birth_year'] is not None or meta_b['death_year'] is not None)
                    if compatible and both_dated:
                        add_signal(a, b, method='name_plus_years', confidence=0.86, priority=250, auto_eligible=False, positive={'type': 'unicode_name_and_dates', 'comparison_name': normalized, 'a_years': [meta_a['birth_year'], meta_a['death_year']], 'b_years': [meta_b['birth_year'], meta_b['death_year']]})
                    else:
                        add_signal(a, b, method='exact_name', confidence=0.52, priority=200, auto_eligible=False, positive={'type': 'unicode_exact_name', 'comparison_name': normalized})
        for (surname, initial), entities in sorted(by_surname.items()):
            if len(surname) < 4 or not initial:
                continue
            unique_entities = sorted(set(entities))
            for index, a in enumerate(unique_entities):
                for b in unique_entities[index + 1:]:
                    if normalize_name(metadata[a]['label']) == normalize_name(metadata[b]['label']):
                        continue
                    if metadata[a]['origin'] == metadata[b]['origin']:
                        continue
                    if not years_compatible((metadata[a]['birth_year'], metadata[a]['death_year']), (metadata[b]['birth_year'], metadata[b]['death_year'])):
                        continue
                    add_signal(a, b, method='surname_initial', confidence=0.35, priority=100, auto_eligible=False, positive={'type': 'surname_initial', 'surname': surname, 'initial': initial})
        now = utc_now()
        candidates: list[dict[str, object]] = []
        for (a, b), signal in sorted(pair_signals.items()):
            negative, conflicts = self._pair_conflicts(a, b, metadata, identifiers)
            method = str(signal['method'])
            auto = bool(signal['auto_eligible']) and (not conflicts)
            confidence = float(signal['confidence'])
            if conflicts:
                confidence = min(confidence, 0.49)
            candidate_id = stable_id('cand', a, b, method, METHOD_VERSION)
            record = {'candidate_id': candidate_id, 'entity_a': a, 'entity_b': b, 'method': method, 'method_version': METHOD_VERSION, 'confidence': round(confidence, 6), 'auto_eligible': auto, 'positive_evidence': signal['positive'], 'negative_evidence': negative, 'conflict_reasons': sorted(set(conflicts)), 'review_state': 'proposed', 'created_at': now, 'updated_at': now}
            candidates.append(record)
            if apply:
                self.connection.execute('\n                    INSERT INTO identity_v3_candidate\n                      (candidate_id,entity_a,entity_b,method,method_version,confidence,\n                       auto_eligible,positive_evidence_json,negative_evidence_json,\n                       conflict_reasons_json,review_state,created_at,updated_at)\n                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)\n                    ON CONFLICT(entity_a,entity_b,method,method_version) DO UPDATE SET\n                      confidence=excluded.confidence,\n                      auto_eligible=excluded.auto_eligible,\n                      positive_evidence_json=excluded.positive_evidence_json,\n                      negative_evidence_json=excluded.negative_evidence_json,\n                      conflict_reasons_json=excluded.conflict_reasons_json,\n                      updated_at=excluded.updated_at\n                    ', (candidate_id, a, b, method, METHOD_VERSION, confidence, int(auto), stable_json(signal['positive']), stable_json(negative), stable_json(sorted(set(conflicts))), 'proposed', now, now))
        if apply:
            self.connection.commit()
        return candidates

    def list_candidates(self, state: str='proposed', limit: int=100) -> list[dict[str, object]]:
        rows = self.connection.execute("SELECT * FROM identity_v3_candidate\n               WHERE (?='all' OR review_state=?)\n               ORDER BY auto_eligible DESC, confidence DESC, candidate_id\n               LIMIT ?", (state, state, limit)).fetchall()
        return [self._candidate_row(row) for row in rows]

    @staticmethod
    def _candidate_row(row: sqlite3.Row) -> dict[str, object]:
        return {'candidate_id': row['candidate_id'], 'entity_a': row['entity_a'], 'entity_b': row['entity_b'], 'method': row['method'], 'method_version': row['method_version'], 'confidence': row['confidence'], 'auto_eligible': bool(row['auto_eligible']), 'positive_evidence': json.loads(row['positive_evidence_json']), 'negative_evidence': json.loads(row['negative_evidence_json']), 'conflict_reasons': json.loads(row['conflict_reasons_json']), 'review_state': row['review_state'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}
