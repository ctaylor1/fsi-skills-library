"""Evidence helpers for five bounded Phase 3 analytical workflows."""
from decimal import Decimal
from insurance_contract import iso_date
from insurance_foundation import number, profile_issues, sources_for


def text(value):
    return isinstance(value, str) and bool(value.strip())


def rows(value, key):
    if not isinstance(value, list) or any(not isinstance(r, dict) for r in value):
        raise ValueError(f'{key} collection must be a list of objects')
    ids = [r.get(key) for r in value]
    if any(not text(x) for x in ids) or len(set(ids)) != len(ids):
        raise ValueError(f'{key} values must be nonblank and unique')
    return value


def ratio(numerator, denominator):
    return None if numerator is None or denominator is None or denominator == 0 else numerator / denominator


def total(values):
    return None if any(x is None for x in values) else sum(values, Decimal(0))


class Review:
    def __init__(self, doc):
        self.doc, self.data, self.findings = doc, doc['data'], []
        self.profile = self.data.get('profile', {})
        for issue in profile_issues(doc, self.profile):
            self.add('profile-gap', issue)

    def add(self, code, message, row=None, severity='gap'):
        refs = (row or {}).get('source_refs', [])
        self.findings.append({'code': code, 'message': message, 'severity': severity,
                              'source_refs': refs if isinstance(refs, list) and all(text(x) for x in refs) else []})

    def evidence(self, row, label):
        if not isinstance(row, dict):
            raise ValueError(label + ' must be an object')
        issues = sources_for(self.doc, row.get('source_refs'))
        for issue in issues:
            self.add('source-gap', label + ': ' + issue)
        return not issues

    def num(self, row, key, *, signed=False, positive=False):
        value = number(row.get(key))
        if value is None:
            self.add('amount-gap', key + ' is unknown', row)
        elif (not signed and value < 0) or (positive and value <= 0):
            raise ValueError(key + ' is outside the supported numeric range')
        return value

    def date(self, row, key):
        if row.get(key) is None:
            self.add('date-gap', key + ' is unknown', row)
            return None
        return iso_date(row[key])

    def scope(self, row, expected, keys):
        valid = True
        for key in keys:
            if row.get(key) != expected.get(key) or not text(row.get(key)):
                self.add('scope-gap', key + ' differs from or is absent in the analysis scope', row)
                valid = False
        return valid

    def finish(self, results):
        gap = any(f['severity'] == 'gap' for f in self.findings)
        review = any(f['severity'] == 'review' for f in self.findings)
        return {'status': 'needs-data' if gap else 'needs-review' if review else 'ready-for-review',
                'findings': self.findings, 'results': results,
                'completeness': 'partial' if gap else 'complete',
                'evaluability': 'partial' if gap else 'evaluable'}


def validate_with(evaluate, doc):
    try:
        evaluate(doc)
        return []
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
        return [str(exc)]
