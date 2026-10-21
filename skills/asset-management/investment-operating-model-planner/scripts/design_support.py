"""Evidence and strict arithmetic helpers for bounded design/measurement jobs."""
from decimal import Decimal
from workflow_contract import iso_date, timestamp, stable_hash
from workflow_foundation import number, profile_issues, sources_for


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {'unknown', 'n/a', 'na'}


def total(values):
    values = list(values)
    return None if any(v is None for v in values) else sum(values, Decimal(0))


def ratio(a, b):
    return None if a is None or b is None or b == 0 else a / b


def ordered(nodes, edges):
    """Deterministic topological order; no inferred repair of missing/cyclic edges."""
    ids = set(nodes)
    if any(a not in ids or b not in ids for a, b in edges):
        return None
    incoming = {n: set() for n in nodes}
    for a, b in edges:
        incoming[b].add(a)
    result = []
    while incoming:
        ready = sorted(n for n, deps in incoming.items() if not deps)
        if not ready:
            return None
        result.extend(ready)
        for n in ready:
            del incoming[n]
        for deps in incoming.values():
            deps.difference_update(ready)
    return result


class Review:
    def __init__(self, doc, method):
        self.doc, self.data, self.findings = doc, doc['data'], []
        self.profile = self.data.get('profile')
        if self.profile is not None and not isinstance(self.profile, dict):
            raise ValueError('profile must be an object or null')
        for issue in profile_issues(doc, self.profile):
            self.add('profile', issue)
        self.profile = self.profile or {}
        if self.profile.get('method') != method or not text(self.profile.get('reviewed_by')):
            self.add('method', 'An explicitly reviewed supported method profile is required')
        for value in doc['context'].values():
            if not text(value):
                self.add('context', 'Actual case scope and professional capacity are unresolved')
        for source in doc['sources']:
            day = source.get('as_of')
            if day is None or iso_date(day) > iso_date(doc['as_of']):
                self.add('source-date', 'Every source needs a date no later than review as_of')
        if doc['unresolved_issues']:
            self.add('inherited-uncertainty', 'Unclassified input issues withhold dependent measures and recommendations')
        mappings = doc.get('context_mappings', [])
        if not isinstance(mappings, list):
            mappings = []
            self.add('context-mapping', 'Context mappings must be a list')
        scope = ('capacity', 'represented_party', 'object_id', 'jurisdiction', 'line_of_business')
        for upstream in doc.get('upstream_artifacts', []):
            if (upstream.get('unresolved_issues') or upstream.get('completeness') != 'complete'
                    or upstream.get('evaluability') != 'evaluable'):
                self.add('upstream-uncertainty', 'Upstream evidence remains incomplete or unresolved')
            if upstream.get('as_of') and upstream['as_of'] > doc['as_of']:
                self.add('upstream-date', 'Upstream artifact postdates review')
            if any(upstream['context'].get(k) != doc['context'].get(k) for k in scope):
                matches = [m for m in mappings if isinstance(m, dict)
                           and m.get('source_artifact_hash') == stable_hash(upstream)
                           and m.get('source_context') == upstream['context']
                           and m.get('target_context') == doc['context']
                           and text(m.get('reviewed_by')) and text(m.get('basis'))
                           and not sources_for(doc, m.get('source_refs'))]
                self.need(len(matches) == 1, 'context-mapping',
                          'One source-bound reviewed context mapping is required before dependent calculation')
        self.scope_valid = self.clear

    @property
    def clear(self):
        return not any(f['severity'] == 'gap' for f in self.findings)

    def add(self, code, message, row=None, severity='gap'):
        refs = (row or {}).get('source_refs', [])
        if not isinstance(refs, list) or any(not isinstance(v, str) for v in refs):
            refs = []
        self.findings.append({'code': code, 'message': message, 'source_refs': refs, 'severity': severity})

    def need(self, condition, code, message, row=None, severity='gap'):
        if not condition:
            self.add(code, message, row, severity)
        return bool(condition)

    def evidence(self, row, label='Record'):
        if not isinstance(row, dict):
            raise ValueError(label+' must be an object')
        errors = sources_for(self.doc, row.get('source_refs'))
        return self.need(not errors, 'evidence', label+': '+('; '.join(errors) or 'source evidence'), row)

    def rows(self, key, id_key, owner=None, *, nonempty=True):
        parent = self.data if owner is None else owner
        rows = parent.get(key)
        if rows is None:
            self.add('inventory', key+' inventory is unknown')
            return []
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(key+' must be a list of objects')
        if len(rows) > 10000:
            raise ValueError(key+' exceeds supported 10000-row boundary')
        ids = [row.get(id_key) for row in rows]
        if any(not text(i) for i in ids) or len(set(ids)) != len(ids):
            raise ValueError(key+': '+id_key+' must be unique nonempty identities')
        if nonempty and not rows:
            self.add('inventory', key+' requires supplied records')
        for row in rows:
            self.evidence(row, key+'/'+row[id_key])
        return rows

    def fields(self, row, keys):
        return all([self.need(text(row.get(k)), 'field', k+' is unresolved', row) for k in keys])

    def strings(self, row, key, *, nonempty=False):
        value = row.get(key)
        if not isinstance(value, list) or any(not text(x) for x in value) or len(set(value)) != len(value):
            raise ValueError(key+' must be an explicit list of unique nonempty strings')
        self.need(not nonempty or bool(value), 'inventory', key+' cannot be empty', row)
        return value

    def num(self, row, key, *, signed=False, integer=False, proportion=False):
        value = number(row.get(key))
        if value is None:
            self.add('unknown-number', key+' is unknown', row)
        elif (not signed and value < 0) or (integer and value != value.to_integral_value()) or (proportion and value > 1):
            raise ValueError(key+' is outside its documented numeric range')
        return value

    def date(self, row, key, *, future=False):
        value = row.get(key)
        if value is None:
            self.add('date', key+' is unknown', row)
            return None
        day = iso_date(value)
        return day if self.need(future or day <= iso_date(self.doc['as_of']), 'date', key+' postdates review', row) else None

    def moment(self, row, key):
        if row.get(key) is None:
            self.add('timestamp', key+' is unknown', row)
            return None
        value = timestamp(row[key])
        return value if self.need(value.date() <= iso_date(self.doc['as_of']), 'timestamp', key+' is in the future in UTC', row) else None

    def flag(self, row, key):
        value = row.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(key+' must be boolean or null')
        return self.need(value is True, key, key+' lacks affirmative supplied evidence', row)

    def finish(self, results):
        gap = not self.clear
        review = any(f['severity'] == 'review' for f in self.findings)
        return {'status': 'needs-data' if gap else 'needs-review' if review else 'ready-for-review',
                'findings': self.findings, 'results': results, 'completeness': 'partial' if gap else 'complete',
                'evaluability': 'partial' if gap else 'evaluable'}


def validate_with(evaluate, doc):
    try:
        evaluate(doc)
        return []
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
        return [str(exc)]
