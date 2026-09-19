"""Requirements-led provider diligence without treating missing evidence as failure."""
from decimal import Decimal, InvalidOperation, localcontext
from copy import deepcopy

SKILL = 'payment-provider-evaluator'
KINDS = {'inspected', 'proposal', 'assumption', 'unknown'}
UNITS = {'per_attempt', 'per_success', 'monthly_fixed', 'one_time', 'fraction_of_value'}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError('numbers must be decimal strings or integers')
    try:
        n = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('invalid decimal') from exc
    if not n.is_finite() or n < 0:
        raise ValueError('number must be finite and nonnegative')
    return n


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ['data must be an object']
    for key in ('requirements', 'providers'):
        if not isinstance(data.get(key), list) or not data[key]:
            errors.append(key + ' must be a nonempty list')
    if errors:
        return errors
    ids = set()
    for row in data['requirements']:
        if not isinstance(row, dict):
            errors.append('requirement must be an object')
            continue
        rid = row.get('requirement_id')
        if not isinstance(rid, str) or not rid or rid in ids:
            errors.append('requirement_id must be unique and nonempty')
        else:
            ids.add(rid)
        if not isinstance(row.get('mandatory'), bool) or not isinstance(row.get('description'), str):
            errors.append('requirement requires description and mandatory boolean')
        try:
            number(row.get('weight'))
        except ValueError:
            errors.append('requirement weight must be a finite nonnegative decimal')
    provider_ids = set()
    for provider in data['providers']:
        if not isinstance(provider, dict):
            errors.append('provider must be an object')
            continue
        pid = provider.get('provider_id')
        if not isinstance(pid, str) or not pid or pid in provider_ids:
            errors.append('provider_id must be unique and nonempty')
        else:
            provider_ids.add(pid)
        if provider.get('role') not in ('issuer_processor', 'acquirer', 'gateway', 'psp', 'infrastructure'):
            errors.append('provider role must identify a supported evaluation role')
        if not isinstance(provider.get('evidence', []), list) or not isinstance(provider.get('prices', []), list):
            errors.append('provider evidence and prices must be lists')
            continue
        seen = set()
        for row in provider.get('evidence', []):
            if not isinstance(row, dict):
                errors.append('evidence row must be an object')
                continue
            rid = row.get('requirement_id')
            if not isinstance(rid, str) or rid not in ids or rid in seen:
                errors.append('evidence requirement_id must be known and unique per provider')
            else:
                seen.add(rid)
            if row.get('status') not in ('supported', 'unsupported', 'unknown') or row.get('evidence_kind', 'unknown') not in KINDS:
                errors.append('invalid evidence status/evidence_kind')
        prices = set()
        for price in provider.get('prices', []):
            if not isinstance(price, dict):
                errors.append('price must be an object')
                continue
            pid = price.get('price_id')
            if not isinstance(pid, str) or not pid or pid in prices:
                errors.append('price_id must be unique and nonempty per provider')
            else:
                prices.add(pid)
            if price.get('unit') not in UNITS or not isinstance(price.get('scope'), str) or not price.get('scope') or not isinstance(price.get('currency'), str) or len(price['currency']) != 3 or not price['currency'].isupper():
                errors.append('price needs unit, explicit scope and three-letter uppercase currency')
            if price.get('evidence_kind', 'unknown') not in KINDS:
                errors.append('invalid price evidence_kind')
            if price.get('amount') is not None:
                try:
                    number(price['amount'])
                except ValueError:
                    errors.append('invalid price amount')
    if not errors and sum(number(x['weight']) for x in data['requirements']) == 0:
        errors.append('at least one requirement must have positive weight')
    return errors


def analyze(request):
    data = request['data']
    current_sources = {s['source_id'] for s in request['sources'] if not s.get('review_due') or s['review_due'] >= request['as_of']}
    findings, comparisons, groups = [], [], {}
    with localcontext() as ctx:
        ctx.prec = 40
        total = sum(number(x['weight']) for x in data['requirements'])
        for provider in data['providers']:
            evidence = {x['requirement_id']: x for x in provider.get('evidence', [])}
            rows, blockers, questions = [], [], []
            supported = unknown = Decimal(0)
            for requirement in data['requirements']:
                row = evidence.get(requirement['requirement_id'], {})
                inspected = row.get('evidence_kind') == 'inspected' and bool(row.get('source_ids')) and set(row['source_ids']).issubset(current_sources)
                state = row.get('status', 'unknown') if inspected else 'unknown'
                weight = number(requirement['weight'])
                if state == 'supported':
                    supported += weight
                elif state == 'unknown':
                    unknown += weight
                if requirement['mandatory'] and state != 'supported':
                    blockers.append({'requirement_id': requirement['requirement_id'], 'status': state})
                if state != 'supported':
                    questions.append({'requirement_id': requirement['requirement_id'], 'question': 'Provide scope-specific evidence and remediation/contract response for: ' + requirement['description']})
                    findings.append({'code': 'provider-evidence-gap', 'message': provider['provider_id'] + '/' + requirement['requirement_id'] + ': ' + state,
                                     'severity': 'gap' if requirement['mandatory'] else 'warning', 'source_ids': row.get('source_ids', [])})
                rows.append({'requirement_id': requirement['requirement_id'], 'requirement': requirement['description'], 'mandatory': requirement['mandatory'],
                             'weight': str(weight), 'asserted_status': row.get('status', 'unknown'), 'evidence_status': state,
                             'evidence_kind': row.get('evidence_kind', 'unknown'), 'source_ids': row.get('source_ids', [])})
            low, high = supported / total * 100, (supported + unknown) / total * 100
            comparisons.append({'provider_id': provider['provider_id'], 'role': provider['role'], 'requirement_matrix': rows,
                                'mandatory_gaps': blockers, 'shortlist_eligible': not blockers,
                                'weighted_score': str(low) if unknown == 0 else None,
                                'score_bounds': {'minimum': str(low), 'maximum': str(high)},
                                'unknown_weight': str(unknown), 'diligence_questions': questions, 'prices': deepcopy(provider.get('prices', []))})
            for price in provider.get('prices', []):
                key = (price['currency'], price['unit'], price['scope'])
                comparable = price.get('amount') is not None and price.get('evidence_kind') == 'inspected' and bool(price.get('source_ids')) and set(price['source_ids']).issubset(current_sources)
                groups.setdefault(key, []).append({'provider_id': provider['provider_id'], 'price_id': price['price_id'],
                                                  'amount': str(number(price['amount'])) if comparable else None,
                                                  'comparison_state': 'supplied-inspected-rate' if comparable else 'unresolved',
                                                  'source_ids': price.get('source_ids', [])})
                if not comparable:
                    findings.append({'code': 'provider-price-gap', 'message': provider['provider_id'] + '/' + price['price_id'] + ': proposal, missing rate or absent inspected source cannot establish comparable cost.', 'severity': 'gap', 'source_ids': price.get('source_ids', [])})
            if not provider.get('prices'):
                findings.append({'code': 'provider-price-gap', 'message': provider['provider_id'] + ': no pricing evidence supplied.', 'severity': 'gap', 'source_ids': []})
    return {'result': {'requirements': deepcopy(data['requirements']), 'provider_comparisons': comparisons,
                       'shortlist_for_human_diligence': [x['provider_id'] for x in comparisons if x['shortlist_eligible']],
                       'selected_provider': None, 'ranking': None,
                       'comparable_rate_groups': [{'currency': key[0], 'unit': key[1], 'scope': key[2], 'rates': rows} for key, rows in sorted(groups.items())],
                       'decision_conditions': ['Mandatory gaps cannot be offset by a weighted score.', 'Inspected is a supplied evidence classification, not independent source authentication.', 'Rate groups do not establish total cost; volumes, inclusions, minimums, tiers, tax, FX and terms require an economics model.', 'Shortlist indicates requirement evidence only; commercial, regulatory and third-party-risk acceptance remains open.']},
            'findings': findings,
            'handoffs': [{'target_skill': 'payment-economics-modeler', 'reason': 'Model comparable participant-specific total economics with explicit volume and cost assumptions.', 'required_inputs': ['requirements', 'provider_comparisons', 'comparable_rate_groups']}]}
