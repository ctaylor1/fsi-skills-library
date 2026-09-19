"""Local structural and evidence checks; supplied profiles are not authenticated."""
from decimal import Decimal

from insurance_contract import iso_date
from insurance_foundation import number, profile_issues, sources_for


def validate_shape(doc, arrays=(), objects=(), numbers=(), dates=(), lists=(), booleans=()):
    data, errors = doc.get('data', {}), []
    for field in arrays:
        if field in data and (not isinstance(data[field], list) or any(not isinstance(r, dict) for r in data[field])):
            errors.append(f'data.{field} must be an array of objects')
    for field in ('profile',) + tuple(objects):
        if field in data and not isinstance(data[field], dict):
            errors.append(f'data.{field} must be an object')
    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        if not isinstance(value, dict):
            return
        for key, item in value.items():
            if key in numbers:
                try:
                    n = number(item)
                    if n is not None and n < 0:
                        errors.append(f'{key} must be nonnegative')
                except (TypeError, ValueError):
                    errors.append(f'{key} must be a finite nonnegative number or null')
            elif key in dates and item is not None:
                try:
                    iso_date(item)
                except (TypeError, ValueError):
                    errors.append(f'{key} must be a calendar date or null')
            elif key in booleans and item is not None and type(item) is not bool:
                errors.append(f'{key} must be boolean or null')
            elif key in lists and (not isinstance(item, list) or any(not isinstance(x, str) or not x.strip() for x in item)):
                errors.append(f'{key} must be an array of nonempty strings')
            elif (key.endswith('_id') or key in ('currency', 'basis', 'kind', 'capacity', 'disposition', 'reviewed_by', 'source_version', 'class_code', 'manual_version', 'method', 'owner', 'from_holder', 'to_holder', 'right_type', 'benefit_type', 'earning_trigger', 'trigger_evidence', 'assessed_by', 'assessor_role', 'initial_holder', 'content_digest', 'stance', 'description', 'question', 'innocent_alternative', 'collection_basis', 'authority_basis', 'referral_question', 'investigation_owner', 'rights_basis', 'task', 'purpose', 'actor', 'explanation', 'reasoning', 'provision', 'reason_text', 'request_text', 'locator', 'recipient', 'route', 'deadline_basis', 'chargeback_basis')) and item is not None and not isinstance(item, str):
                errors.append(f'{key} must be text or null')
            walk(item)
    walk(data)
    return errors


class Review:
    def __init__(self, doc, method):
        self.doc, self.findings = doc, []
        self.profile = doc['data'].get('profile', {})
        self.evidence(self.profile, 'Method profile')
        for issue in profile_issues(doc, self.profile):
            self.add('profile', issue, self.profile)
        if not self.profile.get('reviewed_by') or self.profile.get('method') != method:
            self.add('method', 'Named profile reviewer and supported explicit method are required.', self.profile)

    @property
    def clear(self):
        return not any(f['severity'] == 'gap' for f in self.findings)

    def add(self, code, message, row=None, severity='gap'):
        refs = (row or {}).get('source_refs', [])
        if not isinstance(refs, list) or any(not isinstance(x, str) or not x for x in refs):
            refs = []
        self.findings.append({'code': code, 'message': message, 'source_refs': refs, 'severity': severity})

    def evidence(self, row, label):
        issues = sources_for(self.doc, row.get('source_refs'))
        available = {s['source_ref']: s for s in self.doc['sources']}
        for ref in row.get('source_refs', []) if isinstance(row.get('source_refs'), list) else []:
            source = available.get(ref, {})
            if source.get('as_of') and source['as_of'] > self.doc['as_of']:
                issues.append('source postdates review')
        if issues:
            self.add('evidence', label + ': ' + '; '.join(issues), row)
        return not issues

    def unique(self, rows, key):
        ids = [r.get(key) for r in rows]
        valid = all(isinstance(v, str) and v.strip() for v in ids)
        if not valid or len(set(ids)) != len(ids):
            self.add('duplicate-identity', f'{key} values must be nonempty and unique.')
            return False
        return True

    def date(self, value, label, row=None, future=False):
        try:
            day = iso_date(value)
            if not future and day > iso_date(self.doc['as_of']):
                raise ValueError('future date')
            return day
        except (ValueError, TypeError):
            self.add('date', label + ' missing, invalid or outside as_of scope.', row)
            return None

    def required(self, value, label, row=None):
        if value is None:
            self.add('unknown', label + ' is unknown; zero cannot substitute.', row)
        return value

    def finish(self, results):
        gaps = not self.clear
        reviews = any(f['severity'] == 'review' for f in self.findings)
        return {'status': 'needs-data' if gaps else 'needs-review' if reviews else 'ready-for-review',
                    'findings': self.findings, 'results': results, 'completeness': 'partial' if gaps else 'complete',
                    'evaluability': 'partial' if gaps else 'evaluable'}


def total(values):
    return sum(values, Decimal(0))
