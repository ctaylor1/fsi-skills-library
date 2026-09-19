"""Local draft-review guards. These checks do not authenticate supplied evidence."""
from insurance_contract import iso_date
from insurance_foundation import number, profile_issues, sources_for


def text(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {'unknown', 'n/a', 'na'}


def shape(doc, *, objects=(), lists=(), numbers=(), nonnegative=()):
    data, errors = doc.get('data', {}), []
    for key in objects:
        if key in data and not isinstance(data[key], dict):
            errors.append(f'data.{key} must be an object')
    for key in lists:
        if key in data and (not isinstance(data[key], list) or any(not isinstance(r, dict) for r in data[key])):
            errors.append(f'data.{key} must be a list of objects')
    string_lists = {'source_refs', 'jurisdictions', 'lines_of_business', 'perils', 'component_ids', 'risk_ids', 'scenario_ids', 'entity_ids', 'required_sections'}
    numeric = set(numbers) | set(nonnegative)
    string_fields = {'object_id', 'entity_id', 'portfolio_id', 'row_id', 'account_id', 'policy_id', 'location_id', 'component_id', 'event_id', 'year_id', 'occurrence_id', 'journal_id', 'line_id', 'scenario_id', 'risk_id', 'section_id', 'threshold_id', 'horizon', 'currency', 'basis', 'method', 'valuation_date', 'as_of', 'date', 'start', 'end', 'approved_by', 'reviewed_by', 'owner', 'profile_id', 'version', 'adoption_ref', 'legal_basis_kind', 'denominator_name', 'aggregation_method', 'sign_convention', 'normal_side', 'metric_id', 'purpose', 'status', 'geocode_quality', 'model_quality', 'model_version', 'model_id', 'materiality_basis', 'assessment', 'conclusion', 'governance_role', 'decision', 'evidence_date', 'required_capital_basis', 'available_capital_basis', 'unit'}
    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in numeric:
                    try:
                        n = number(item)
                        if n is not None and key in nonnegative and n < 0:
                            errors.append(f'{path}.{key} must be nonnegative')
                    except ValueError as exc:
                        errors.append(f'{path}.{key}: {exc}')
                elif key in string_lists and (not isinstance(item, list) or any(not isinstance(s, str) or not s.strip() for s in item)):
                    errors.append(f'{path}.{key} must be a list of nonempty strings')
                elif key in string_fields and item is not None and not isinstance(item, str):
                    errors.append(f'{path}.{key} must be a string or null')
                walk(item, path + '.' + key)
        elif isinstance(value, list):
            if len(value) > 10000:
                errors.append(f'{path} exceeds the 10000 row offline bound')
            for index, item in enumerate(value):
                walk(item, f'{path}[{index}]')
    walk(data, 'data')
    return errors


class Review:
    def __init__(self, doc):
        self.doc, self.findings, self.blocked = doc, [], False

    def add(self, code, message, row=None, *, block=True, severity='gap'):
        self.blocked |= block
        refs = (row or {}).get('source_refs', [])
        if not isinstance(refs, list) or any(not text(s) for s in refs):
            refs = []
        self.findings.append({'code': code, 'message': message, 'severity': severity, 'source_refs': refs})
        return False

    def check(self, condition, code, message, row=None, **kwargs):
        return True if condition else self.add(code, message, row, **kwargs)

    def evidence(self, row, label, *, block=True):
        issues = sources_for(self.doc, row.get('source_refs'))
        refs = row.get('source_refs', [])
        for source in self.doc['sources']:
            if source['source_ref'] in refs and source.get('as_of', self.doc['as_of']) > self.doc['as_of']:
                issues.append('source postdates requested as_of')
        return self.check(not issues, label + '-source', '; '.join(issues), row, block=block)

    def date(self, value, label, *, equal=None, latest=None, row=None, block=True):
        try:
            day = iso_date(value)
            if equal is not None and day != iso_date(equal):
                raise ValueError('date differs from required valuation date')
            if latest is not None and day > iso_date(latest):
                raise ValueError('date is after review cutoff')
            return day
        except (ValueError, TypeError):
            self.add(label + '-date', 'Require a valid calendar date consistent with valuation and review cutoff.', row, block=block)
            return None

    def profile(self, method):
        data = self.doc['data']
        p = data.get('profile', {})
        for issue in profile_issues(self.doc, p):
            self.add('profile-scope', issue, p)
        self.evidence(p, 'profile')
        self.check(text(p.get('approved_by')), 'profile-approval', 'Supply the accountable methodology reviewer; a name is not authenticated approval.', p)
        self.check(p.get('method') == method and data.get('method') == method, 'method-scope', 'The supplied profile and data must select this supported method.', p)
        kind = p.get('legal_basis_kind')
        self.check(kind in {'internal-methodology', 'reviewed-applicable-law'}, 'profile-legal-scope', 'Distinguish an internal method from reviewed jurisdictional adoption.', p)
        if kind == 'reviewed-applicable-law':
            ref = p.get('adoption_ref')
            self.check(text(ref) and not sources_for(self.doc, [ref]), 'profile-adoption', 'Reviewed law requires a supplied versioned adoption source; a model law or professional standard is not local adoption.', p)
        self.check(text(data.get('basis')) and p.get('basis') == data.get('basis'), 'basis-scope', 'Data and reviewed methodology must share an explicit measurement basis.', p)
        self.check(text(data.get('object_id')) and data.get('object_id') == self.doc['context']['object_id'], 'object-scope', 'Bind the native portfolio/entity to context.object_id.')
        self.date(data.get('valuation_date'), 'valuation', latest=self.doc['as_of'])
        return p

    def bind(self, row, label, *, currency=True):
        d = self.doc['data']
        ok = self.evidence(row, label)
        ok &= self.check(row.get('object_id') == d.get('object_id') and row.get('basis') == d.get('basis'), label + '-scope', 'Each record must retain the same object and measurement basis.', row)
        if currency:
            ok &= self.check(text(d.get('currency')) and row.get('currency') == d.get('currency'), label + '-currency', 'Amounts require one explicit shared currency; no inferred FX conversion.', row)
        ok &= self.date(row.get('valuation_date'), label, equal=d.get('valuation_date'), row=row) is not None
        return ok

    def result(self, results):
        return {'status': 'needs-data' if self.blocked else 'needs-review' if any(f['severity'] == 'review' for f in self.findings) else 'ready-for-review', 'findings': self.findings, 'results': results, 'completeness': 'complete', 'evaluability': 'evaluable'}
