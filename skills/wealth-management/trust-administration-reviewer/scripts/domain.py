"""One-trust evidence review and supplied-classification cash reconciliation."""
from copy import deepcopy
from decimal import Decimal

from wealth_contract import iso_date, make_output, nonempty, source_errors
from wealth_workflow import (add, base_errors, base_findings, cited, common_result,
                             dec, enum, money, number, rows, texts, validate_result)

SKILL = 'trust-administration-reviewer'
ZERO = Decimal(0)
REGISTERS = {'documents': 'document_id', 'clauses': 'clause_id', 'fiduciaries': 'fiduciary_id',
             'beneficiaries': 'beneficiary_id', 'authority_reviews': 'authority_id',
             'cash_accounts': 'account_id', 'movements': 'movement_id',
             'reclassifications': 'reclassification_id', 'assets': 'asset_id',
             'obligations': 'obligation_id', 'distribution_requests': 'distribution_id'}
COVERAGE = ('documents', 'fiduciaries', 'beneficiaries', 'cash_accounts', 'movements',
            'reclassifications', 'assets', 'obligations', 'distribution_requests')


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    allowed = {'schema_version', 'request_id', 'household_id', 'as_of', 'engagement', 'sources',
               'policy', 'upstream_issues', 'scope_type', 'trust_id', 'currency', 'period_start',
               'coverage', 'legal_profile', *REGISTERS}
    if set(doc) - allowed:
        errors.append('unsupported top-level fields: ' + ', '.join(sorted(set(doc) - allowed)))
    if doc.get('scope_type') != 'trust' or not nonempty(doc.get('trust_id')) or doc['household_id'] != 'trust:' + str(doc.get('trust_id')):
        errors.append('one trust scope requires trust_id and household_id trust:<trust_id>')
    if doc['engagement']['capacity'] != 'trust' or doc.get('currency') != 'USD':
        errors.append('initial scope requires trust engagement capacity and USD')
    start = iso_date(doc.get('period_start'))
    if start is None or start > iso_date(doc['as_of']):
        errors.append('period_start must be a valid date no later than as_of')

    def text(row, keys, path):
        for key in keys:
            if not nonempty(row.get(key)):
                errors.append(f'{path}.{key} requires nonempty text')

    def amount(row, key, path, nullable=True, signed=False):
        if key not in row or (row[key] is None and not nullable):
            errors.append(f'{path}.{key} is required')
        elif row[key] is not None and (not number(row[key], -10**15 if signed else 0) or dec(row[key]).as_tuple().exponent < -2):
            errors.append(f'{path}.{key} must be a bounded cents amount or explicit null')

    def date(row, key, path, nullable=False, future=False):
        value = row.get(key)
        if key not in row or (value is None and not nullable):
            errors.append(f'{path}.{key} is required')
        elif value is not None and (iso_date(value) is None or (not future and value > doc['as_of'])):
            errors.append(f'{path}.{key} requires a valid ' + ('' if future else 'nonfuture ') + 'ISO date')

    def review(value, path):
        if not isinstance(value, dict):
            errors.append(path + ' must be a review object')
            return
        if not enum(value.get('status'), {'documented', 'incomplete', 'unknown'}):
            errors.append(path + '.status must be documented/incomplete/unknown')
        for key in ('reviewer', 'reference', 'basis'):
            if key not in value or (value[key] is not None and not nonempty(value[key])):
                errors.append(path + '.' + key + ' requires nonempty text or explicit null')
        date(value, 'reviewed_on', path, nullable=True)
        date(value, 'review_by', path, nullable=True, future=True)
        if iso_date(value.get('reviewed_on')) and iso_date(value.get('review_by')) and value['review_by'] < value['reviewed_on']:
            errors.append(path + ' review_by precedes reviewed_on')

    policy = doc['policy']
    if type(policy.get('max_asset_age_days')) is not int or not 1 <= policy['max_asset_age_days'] <= 3660:
        errors.append('policy.max_asset_age_days must be an integer 1..3660')
    if not texts(policy.get('required_packet_types')):
        errors.append('policy.required_packet_types requires a nonempty unique text list')
    if not texts(policy.get('required_authority_powers')) or any(p not in {'administration', 'accounting-review', 'distribution-review'} for p in policy.get('required_authority_powers', []) if isinstance(p, str)):
        errors.append('policy.required_authority_powers requires a nonempty supported unique list')
    coverage = doc.get('coverage')
    if not isinstance(coverage, dict):
        errors.append('coverage requires an explicit object')
    else:
        for key in COVERAGE:
            if key not in coverage or (coverage[key] is not None and type(coverage[key]) is not bool):
                errors.append(f'coverage.{key} must be explicit boolean/null')
    for register, identifier in REGISTERS.items():
        for record in rows(doc, register, errors, identifier):
            if record.get('trust_id') != doc.get('trust_id'):
                errors.append(register + ' record must identify the same trust_id; cross-trust aggregation is unsupported')
    if errors:
        return errors
    maps = {register: {r[key]: r for r in doc[register]} for register, key in REGISTERS.items()}

    def link(row, key, register, path, many=False, empty=False):
        value = row.get(key)
        if many:
            if not texts(value, allow_empty=empty):
                errors.append(f'{path}.{key} must be an explicit unique ID list')
                return
            values = value
        elif nonempty(value):
            values = [value]
        else:
            errors.append(f'{path}.{key} requires an existing ID')
            return
        if any(v not in maps[register] for v in values):
            errors.append(f'{path}.{key} references unknown {register}')

    profile = doc.get('legal_profile')
    review(profile, 'legal_profile')
    if isinstance(profile, dict):
        for key in ('governing_law', 'precedence_statement'):
            if key not in profile or (profile[key] is not None and not nonempty(profile[key])):
                errors.append(f'legal_profile.{key} requires text or explicit null')
        link(profile, 'document_ids', 'documents', 'legal_profile', many=True, empty=True)
    for d in doc['documents']:
        text(d, ('title', 'kind'), 'documents')
        date(d, 'effective_on', 'documents')
    for c in doc['clauses']:
        link(c, 'document_id', 'documents', 'clauses')
        text(c, ('locator', 'excerpt'), 'clauses')
        if not enum(c.get('topic'), {'authority', 'distribution', 'accounting', 'reporting', 'other'}):
            errors.append('clause topic is unsupported')
    for f in doc['fiduciaries']:
        text(f, ('masked_name', 'role_description'), 'fiduciaries')
        review(f.get('appointment_review'), 'fiduciaries.appointment_review')
    for b in doc['beneficiaries']:
        text(b, ('masked_name', 'interest_description', 'household_id'), 'beneficiaries')
        if isinstance(b.get('household_id'), str) and b['household_id'].startswith(('trust:', 'book:', 'family:')):
            errors.append('beneficiary household_id must be an actual household ID, not a collection marker')
        link(b, 'clause_ids', 'clauses', 'beneficiaries', many=True, empty=True)
        review(b.get('record_review'), 'beneficiaries.record_review')
    for a in doc['authority_reviews']:
        link(a, 'fiduciary_ids', 'fiduciaries', 'authority_reviews', many=True, empty=True)
        link(a, 'clause_ids', 'clauses', 'authority_reviews', many=True, empty=True)
        if not texts(a.get('powers'), allow_empty=True) or any(p not in {'administration', 'accounting-review', 'distribution-review'} for p in a.get('powers', []) if isinstance(p, str)):
            errors.append('authority powers require supported explicit list')
        if a.get('joint_action_rule') is not None and not nonempty(a.get('joint_action_rule')):
            errors.append('joint_action_rule requires text or null')
        review(a.get('legal_review'), 'authority_reviews.legal_review')
    for account in doc['cash_accounts']:
        text(account, ('label',), 'cash_accounts')
        amount(account, 'protected_reserve', 'cash_accounts')
        for key in ('opening', 'closing'):
            snapshot = account.get(key)
            if not isinstance(snapshot, dict):
                errors.append(f'cash_accounts.{key} must be object')
                continue
            for part in ('total', 'principal', 'income'):
                amount(snapshot, part, 'cash_accounts.' + key)
            if snapshot.get('date') != (doc['period_start'] if key == 'opening' else doc['as_of']) or snapshot.get('basis') != ('before-period-movements' if key == 'opening' else 'after-period-movements'):
                errors.append('cash snapshot date/basis must match its opening or closing period boundary')
            if all(number(snapshot.get(k)) for k in ('total', 'principal', 'income')) and dec(snapshot['total']) != dec(snapshot['principal']) + dec(snapshot['income']):
                errors.append('cash snapshot principal + income must equal total when known')
    for m in doc['movements']:
        link(m, 'account_id', 'cash_accounts', 'movements')
        if not enum(m.get('kind'), {'receipt', 'expense', 'distribution', 'asset-purchase', 'asset-sale', 'cash-transfer'}):
            errors.append('unsupported cash movement kind')
        if not enum(m.get('direction'), {'inflow', 'outflow'}) or not enum(m.get('lifecycle'), {'settled', 'pending', 'cancelled'}):
            errors.append('movement requires explicit direction and lifecycle')
        date(m, 'date', 'movements', future=m.get('lifecycle') != 'settled')
        if iso_date(m.get('date')) and m.get('lifecycle') == 'settled' and m['date'] < doc['period_start']:
            errors.append('settled movement predates the opening cash snapshot')
        amount(m, 'amount', 'movements', nullable=False)
        if number(m.get('amount')) and dec(m['amount']) <= 0:
            errors.append('movement amount must be positive')
        alloc = m.get('allocation')
        if not isinstance(alloc, dict):
            errors.append('movement allocation requires explicit object')
        else:
            amount(alloc, 'principal', 'movements.allocation')
            amount(alloc, 'income', 'movements.allocation')
            review(alloc.get('review'), 'movements.allocation.review')
            if all(number(alloc.get(k)) for k in ('principal', 'income')) and number(m.get('amount')) and dec(alloc['principal']) + dec(alloc['income']) != dec(m['amount']):
                errors.append('movement principal + income allocation must equal cash amount')
        if m.get('kind') in {'expense', 'distribution', 'asset-purchase'} and m.get('direction') != 'outflow':
            errors.append('expense/distribution/purchase must be cash outflow')
        if m.get('kind') in {'receipt', 'asset-sale'} and m.get('direction') != 'inflow':
            errors.append('receipt/sale must be cash inflow')
        if m.get('kind') == 'distribution':
            link(m, 'distribution_id', 'distribution_requests', 'movements')
        elif m.get('distribution_id') is not None or 'distribution_id' not in m:
            errors.append('non-distribution movement needs explicit null distribution_id')
        if m.get('kind') == 'cash-transfer':
            text(m, ('transfer_id',), 'movements')
            if m.get('cash_flow_scope') != 'within-trust-cash':
                errors.append('cash-transfer must be within-trust-cash')
        elif m.get('cash_flow_scope') != ('cash-asset-conversion' if m.get('kind') in {'asset-purchase', 'asset-sale'} else 'outside-trust-cash') or m.get('transfer_id') is not None or 'transfer_id' not in m:
            errors.append('movement requires matching cash boundary and null transfer_id; this is not performance external-flow classification')
    for r in doc['reclassifications']:
        link(r, 'account_id', 'cash_accounts', 'reclassifications')
        date(r, 'date', 'reclassifications', future=r.get('lifecycle') != 'settled')
        if iso_date(r.get('date')) and r.get('lifecycle') == 'settled' and r['date'] < doc['period_start']:
            errors.append('settled reclassification predates opening snapshot')
        amount(r, 'amount', 'reclassifications')
        if not enum(r.get('lifecycle'), {'settled', 'pending', 'cancelled'}) or not enum(r.get('from_bucket'), {'principal', 'income'}):
            errors.append('reclassification requires explicit lifecycle and from_bucket')
        review(r.get('classification_review'), 'reclassifications.classification_review')
    cash_asset_accounts = []
    for a in doc['assets']:
        text(a, ('description',), 'assets')
        if not enum(a.get('kind'), {'cash', 'noncash'}):
            errors.append('asset kind must distinguish cash/noncash')
        amount(a, 'reported_value', 'assets')
        date(a, 'valuation_date', 'assets', nullable=True)
        if a.get('kind') == 'cash':
            link(a, 'account_id', 'cash_accounts', 'assets')
            if nonempty(a.get('account_id')):
                cash_asset_accounts.append(a['account_id'])
        elif a.get('account_id') is not None or 'account_id' not in a:
            errors.append('noncash assets require explicit null account_id')
    if len(cash_asset_accounts) != len(set(cash_asset_accounts)):
        errors.append('duplicate cash-asset/account reference would double count cash')
    for o in doc['obligations']:
        text(o, ('description',), 'obligations')
        link(o, 'clause_ids', 'clauses', 'obligations', many=True, empty=True)
        link(o, 'owner_fiduciary_id', 'fiduciaries', 'obligations')
        date(o, 'due_on', 'obligations', nullable=True, future=True)
        date(o, 'completed_on', 'obligations', nullable=True)
        if not enum(o.get('status'), {'open', 'completed', 'unknown'}):
            errors.append('obligation status must be open/completed/unknown')
        if o.get('completion_reference') is not None and not nonempty(o.get('completion_reference')):
            errors.append('completion_reference requires text or null')
        if o.get('status') != 'completed' and o.get('completed_on') is not None:
            errors.append('open/unknown obligation cannot claim completion date')
    for r in doc['distribution_requests']:
        link(r, 'beneficiary_id', 'beneficiaries', 'distribution_requests')
        link(r, 'account_id', 'cash_accounts', 'distribution_requests')
        link(r, 'clause_ids', 'clauses', 'distribution_requests', many=True, empty=True)
        link(r, 'authority_ids', 'authority_reviews', 'distribution_requests', many=True, empty=True)
        text(r, ('purpose',), 'distribution_requests')
        date(r, 'requested_on', 'distribution_requests')
        date(r, 'needed_by', 'distribution_requests', nullable=True, future=True)
        if iso_date(r.get('requested_on')) and iso_date(r.get('needed_by')) and r['needed_by'] < r['requested_on']:
            errors.append('distribution needed_by predates request')
        if not enum(r.get('lifecycle'), {'proposed', 'partially-settled', 'settled', 'withdrawn'}):
            errors.append('distribution request lifecycle is invalid')
        for key in ('amount', 'paid_before_period', 'requested_principal', 'requested_income'):
            amount(r, key, 'distribution_requests')
        if all(number(r.get(k)) for k in ('amount', 'requested_principal', 'requested_income')) and dec(r['requested_principal']) + dec(r['requested_income']) != dec(r['amount']):
            errors.append('requested principal plus income must equal requested amount; this is request intent only')
        if iso_date(r.get('requested_on')) and r['requested_on'] >= doc['period_start'] and number(r.get('paid_before_period')) and dec(r['paid_before_period']) != 0:
            errors.append('request made in-period cannot have prior-period payments')
        review(r.get('conflict_review'), 'distribution_requests.conflict_review')
        if not enum(r.get('conflict_state'), {'none-identified', 'open', 'unknown'}):
            errors.append('distribution conflict_state requires explicit reviewed observation')
        packet = rows(r, 'packet', errors, 'type')
        for item in packet:
            text(item, ('description',), 'distribution_requests.packet')
            if not enum(item.get('status'), {'present', 'missing', 'unknown'}):
                errors.append('packet status is invalid')
            if item.get('reference') is not None and not nonempty(item.get('reference')):
                errors.append('packet reference must be text or null')
    if errors:
        return errors
    for transfer in sorted({m['transfer_id'] for m in doc['movements'] if m['kind'] == 'cash-transfer'}):
        legs = [m for m in doc['movements'] if m['transfer_id'] == transfer]
        if len(legs) != 2 or {m['direction'] for m in legs} != {'inflow', 'outflow'} or len({m['account_id'] for m in legs}) != 2:
            errors.append('internal transfer requires exactly two opposite legs in different trust accounts')
        elif any(legs[0][k] != legs[1][k] for k in ('date', 'lifecycle')) or dec(legs[0]['amount']) != dec(legs[1]['amount']):
            errors.append('internal transfer legs must match date, lifecycle and amount; in-transit transfers unsupported')
        elif any((legs[0]['allocation'][k] is None) != (legs[1]['allocation'][k] is None) or (legs[0]['allocation'][k] is not None and dec(legs[0]['allocation'][k]) != dec(legs[1]['allocation'][k])) for k in ('principal', 'income')):
            errors.append('internal transfer allocations must agree; use explicit reclassification separately')
    for r in doc['distribution_requests']:
        linked = [m for m in doc['movements'] if m['distribution_id'] == r['distribution_id']]
        if any(m['account_id'] != r['account_id'] or (m['lifecycle'] == 'settled' and m['date'] < r['requested_on']) for m in linked):
            errors.append('distribution payment account/date conflicts with request')
        period_paid = sum((dec(m['amount']) for m in linked if m['lifecycle'] == 'settled'), ZERO)
        if r['amount'] is not None and r['paid_before_period'] is not None:
            paid = dec(r['paid_before_period']) + period_paid
            requested = dec(r['amount'])
            life = r['lifecycle']
            if paid > requested or (life in {'proposed', 'withdrawn'} and paid != 0) or (life == 'settled' and paid != requested) or (life == 'partially-settled' and not 0 < paid < requested):
                errors.append('distribution lifecycle does not reconcile to prior and current settled payments')
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError('; '.join(errors))
    findings = base_findings(doc)
    result = common_result(doc)
    result.update(scope_type='trust', trust_id=doc['trust_id'], currency='USD', period_start=doc['period_start'])
    result['handoff_context'].update(scope_type='trust', trust_id=doc['trust_id'])
    context_ok = not source_errors(doc['policy'].get('source_ids'), doc) and not source_errors(doc['engagement'].get('source_ids'), doc)
    upstream_clear = all(i['status'] == 'resolved' and not source_errors(i.get('source_ids'), doc)
                         and not source_errors(i['resolution'].get('source_ids'), doc)
                         for i in doc['upstream_issues'])
    coverage_ok = cited(doc['coverage'], doc, findings, 'coverage')
    covered = {k: coverage_ok and doc['coverage'][k] is True for k in COVERAGE}
    for key, known in covered.items():
        if not known:
            add(findings, 'inventory-incomplete', 'Sourced complete ' + key + ' inventory is not established', 'coverage.' + key)
    support = {}; maps = {}
    for register, identifier in REGISTERS.items():
        maps[register] = {r[identifier]: r for r in doc[register]}
        support[register] = {r[identifier]: cited(r, doc, findings, register + '.' + r[identifier]) for r in doc[register]}
    for register in ('documents', 'fiduciaries', 'beneficiaries', 'cash_accounts', 'assets'):
        if not doc[register]:
            add(findings, 'empty-inventory', 'Trust review needs a substantive ' + register + ' inventory', register)

    def reviewed(row, path):
        supported = cited(row, doc, findings, path)
        complete = supported and row['status'] == 'documented' and all(nonempty(row.get(k)) for k in ('reviewer', 'reference', 'basis')) and row['reviewed_on'] is not None and row['review_by'] is not None and row['review_by'] >= doc['as_of']
        if not complete:
            add(findings, 'review-evidence-gap', 'Current attributed substantive review evidence is incomplete', path)
        return complete

    profile = doc['legal_profile']
    profile_reviewed = reviewed(profile, 'legal_profile')
    profile_ok = context_ok and upstream_clear and profile_reviewed and covered['documents'] and bool(doc['documents']) and set(profile['document_ids']) == set(maps['documents']) and all(support['documents'].values()) and nonempty(profile.get('governing_law')) and nonempty(profile.get('precedence_statement'))
    if not profile_ok:
        add(findings, 'legal-profile-gap', 'Obtain a current attributed applicable-law and document-precedence review covering every supplied governing document', 'legal_profile')
    result['legal_profile_review'] = dict(record=deepcopy(profile), evidence_status='documented-for-human-review' if profile_ok else 'incomplete', legal_applicability_decision='not-determined')
    def clauses_ok(ids, topic=None):
        return bool(ids) and profile_ok and all(support['clauses'][cid] and support['documents'][maps['clauses'][cid]['document_id']] for cid in ids) and (topic is None or any(maps['clauses'][cid]['topic'] == topic for cid in ids))

    fiduciary_ok = {}
    for f in doc['fiduciaries']:
        check = reviewed(f['appointment_review'], 'fiduciaries.' + f['fiduciary_id'] + '.appointment_review')
        fiduciary_ok[f['fiduciary_id']] = support['fiduciaries'][f['fiduciary_id']] and check and profile_ok and covered['fiduciaries']
    beneficiary_ok = {}
    for b in doc['beneficiaries']:
        check = reviewed(b['record_review'], 'beneficiaries.' + b['beneficiary_id'] + '.record_review')
        beneficiary_ok[b['beneficiary_id']] = support['beneficiaries'][b['beneficiary_id']] and check and clauses_ok(b['clause_ids']) and covered['beneficiaries']
        if not beneficiary_ok[b['beneficiary_id']]:
            add(findings, 'beneficiary-record-gap', 'Beneficiary identity/household link and cited interest evidence need human review; no entitlement inferred', 'beneficiaries.' + b['beneficiary_id'])
    authority_ok = {}; authority_results = []
    for a in doc['authority_reviews']:
        review_ok = reviewed(a['legal_review'], 'authority_reviews.' + a['authority_id'] + '.legal_review')
        qualified = support['authority_reviews'][a['authority_id']] and review_ok and bool(a['fiduciary_ids']) and all(fiduciary_ok[x] for x in a['fiduciary_ids']) and clauses_ok(a['clause_ids'], 'authority') and nonempty(a.get('joint_action_rule')) and bool(a['powers'])
        authority_ok[a['authority_id']] = qualified
        if not qualified:
            add(findings, 'authority-evidence-gap', 'Cited appointment, authority clauses and attributed legal review of powers/joint action are required; a trustee title is insufficient', 'authority_reviews.' + a['authority_id'])
        authority_results.append(dict(record=deepcopy(a), evidence_status='documented-for-human-review' if qualified else 'incomplete', permission_authenticated=False))
    for power in doc['policy']['required_authority_powers']:
        if not any(authority_ok[a['authority_id']] and power in a['powers'] for a in doc['authority_reviews']):
            add(findings, 'trust-authority-review-gap', 'Supplied policy requires documented authority evidence for ' + power, 'authority_reviews', power=power)
    result['documents'] = deepcopy(doc['documents']); result['clauses'] = deepcopy(doc['clauses'])
    result['fiduciaries'] = deepcopy(doc['fiduciaries']); result['beneficiaries'] = deepcopy(doc['beneficiaries'])
    result['authority_reviews'] = authority_results

    allocation_ok = {}
    for m in doc['movements']:
        alloc = m['allocation']
        cited_alloc = cited(alloc, doc, findings, 'movements.' + m['movement_id'] + '.allocation')
        reviewed_alloc = reviewed(alloc['review'], 'movements.' + m['movement_id'] + '.allocation.review')
        allocation_ok[m['movement_id']] = profile_ok and cited_alloc and reviewed_alloc and alloc['principal'] is not None and alloc['income'] is not None
        if not allocation_ok[m['movement_id']]:
            add(findings, 'classification-unknown', 'Principal/income allocation requires explicit amounts and supported human classification; no tax or legal classification inferred', 'movements.' + m['movement_id'])
    reclass_ok = {}
    for r in doc['reclassifications']:
        reviewed_reclass = reviewed(r['classification_review'], 'reclassifications.' + r['reclassification_id'] + '.classification_review')
        reclass_ok[r['reclassification_id']] = profile_ok and support['reclassifications'][r['reclassification_id']] and reviewed_reclass and r['amount'] is not None
        if not reclass_ok[r['reclassification_id']]:
            add(findings, 'classification-unknown', 'Reclassification requires an explicit amount and supported human review', 'reclassifications.' + r['reclassification_id'])
    reconciliations = []; cash_closing = {}; reconciled_total = {}
    for a in doc['cash_accounts']:
        aid = a['account_id']; path = 'cash_accounts.' + aid
        opening_ok = cited(a['opening'], doc, findings, path + '.opening')
        closing_ok = cited(a['closing'], doc, findings, path + '.closing')
        relevant = [m for m in doc['movements'] if m['account_id'] == aid and m['lifecycle'] == 'settled']
        adjustments = [r for r in doc['reclassifications'] if r['account_id'] == aid and r['lifecycle'] == 'settled']
        base_ok = context_ok and support['cash_accounts'][aid] and covered['cash_accounts'] and covered['movements'] and opening_ok and closing_ok and all(support['movements'][m['movement_id']] for m in relevant)
        parts = {}
        for part in ('total', 'principal', 'income'):
            opening = a['opening'][part]; closing = a['closing'][part]
            known = base_ok and opening is not None and closing is not None
            if part != 'total':
                known = known and covered['reclassifications'] and all(allocation_ok[m['movement_id']] for m in relevant) and all(reclass_ok[r['reclassification_id']] for r in adjustments)
            expected = difference = None
            if known:
                net = sum(((1 if m['direction'] == 'inflow' else -1) * dec(m['amount'] if part == 'total' else m['allocation'][part]) for m in relevant), ZERO)
                if part != 'total':
                    net += sum(((-1 if r['from_bucket'] == part else 1) * dec(r['amount']) for r in adjustments), ZERO)
                expected = dec(opening) + net
                difference = dec(closing) - expected
                if abs(difference) > dec('0.01'):
                    add(findings, 'cash-reconciliation-difference', f'{part} closing cash differs from opening plus settled classified movements', path + '.' + part, difference=money(difference))
            else:
                add(findings, 'cash-reconciliation-unknown', f'{part} cash reconciliation lacks complete supported amounts, sources or classifications', path + '.' + part)
            parts[part] = dict(observed_opening=deepcopy(opening), observed_closing=deepcopy(closing), expected_closing=None if expected is None else money(expected), difference=None if difference is None else money(difference), reconciled=known and abs(difference) <= dec('0.01'))
        cash_closing[aid] = dec(a['closing']['total']) if context_ok and support['cash_accounts'][aid] and closing_ok and a['closing']['total'] is not None else None
        reconciled_total[aid] = parts['total']['reconciled']
        reconciliations.append(dict(account=deepcopy(a), components=parts, settled_movement_ids=[m['movement_id'] for m in relevant], settled_reclassification_ids=[r['reclassification_id'] for r in adjustments]))
    result['cash_reconciliation'] = reconciliations
    result['movements'] = deepcopy(doc['movements']); result['reclassifications'] = deepcopy(doc['reclassifications'])
    asset_results = []; noncash_values = []; cash_matches = []
    for a in doc['assets']:
        age = None if a['valuation_date'] is None else (iso_date(doc['as_of']) - iso_date(a['valuation_date'])).days
        qualified = context_ok and support['assets'][a['asset_id']] and a['reported_value'] is not None and age is not None and age <= doc['policy']['max_asset_age_days']
        if a['kind'] == 'cash':
            qualified = qualified and a['valuation_date'] == doc['as_of'] and cash_closing[a['account_id']] is not None and abs(dec(a['reported_value']) - cash_closing[a['account_id']]) <= dec('0.01')
            cash_matches.append(qualified)
        else:
            noncash_values.append(dec(a['reported_value']) if qualified else None)
        if not qualified:
            add(findings, 'asset-evidence-gap', 'Value is unknown, stale, uncited or cash inventory does not reconcile to its account closing cash', 'assets.' + a['asset_id'])
        asset_results.append(dict(record=deepcopy(a), age_days=age, evidence_current=qualified, included_separately_in_assets_total=a['kind'] == 'noncash' and qualified))
    cash_ids = {a['account_id'] for a in doc['assets'] if a['kind'] == 'cash'}
    inventory_complete = context_ok and covered['assets'] and covered['cash_accounts'] and bool(doc['cash_accounts']) and cash_ids == set(maps['cash_accounts']) and all(cash_matches) and all(v is not None for v in cash_closing.values()) and all(v is not None for v in noncash_values)
    if cash_ids != set(maps['cash_accounts']):
        add(findings, 'cash-inventory-gap', 'Asset cash references must cover every trust cash account exactly once', 'assets')
    total_cash = sum((v for v in cash_closing.values() if v is not None), ZERO)
    total_noncash = sum((v for v in noncash_values if v is not None), ZERO)
    result['assets'] = asset_results
    result['asset_summary'] = dict(known_cash_subtotal=money(total_cash), known_noncash_subtotal=money(total_noncash), reported_trust_assets_total=money(total_cash + total_noncash) if inventory_complete else None,
                                 complete_supported_inventory=inventory_complete, cash_counted_once=True, valuation_basis='Dated supplied inventory, not a current price model or performance calculation')

    obligation_results = []
    for o in doc['obligations']:
        path = 'obligations.' + o['obligation_id']
        supported = support['obligations'][o['obligation_id']] and clauses_ok(o['clause_ids']) and fiduciary_ok[o['owner_fiduciary_id']]
        complete = supported and o['status'] == 'completed' and o['completed_on'] is not None and nonempty(o.get('completion_reference'))
        state = 'completed-evidence-recorded' if complete else 'unknown' if not supported or o['due_on'] is None or o['status'] in {'unknown', 'completed'} else 'overdue' if o['due_on'] < doc['as_of'] else 'open'
        if state in {'unknown', 'overdue'}:
            add(findings, 'obligation-' + state, 'Review the supplied clause, owner, due date and completion evidence', path)
        obligation_results.append(dict(record=deepcopy(o), review_state=state, completion_authenticated=False))
    result['obligations'] = obligation_results
    requests = []; open_by_account = {a: [] for a in maps['cash_accounts']}
    for r in doc['distribution_requests']:
        rid = r['distribution_id']; path = 'distribution_requests.' + rid
        linked = [m for m in doc['movements'] if m['distribution_id'] == rid and m['lifecycle'] == 'settled']
        observed_paid = sum((dec(m['amount']) for m in linked), ZERO)
        pending = [m for m in doc['movements'] if m['distribution_id'] == rid and m['lifecycle'] == 'pending']
        observed_pending = sum((dec(m['amount']) for m in pending), ZERO)
        supported = context_ok and profile_ok and support['distribution_requests'][rid] and support['cash_accounts'][r['account_id']] and covered['distribution_requests'] and covered['movements'] and all(support['movements'][m['movement_id']] for m in linked)
        remaining = None if not supported or r['amount'] is None or r['paid_before_period'] is None else (ZERO if r['lifecycle'] == 'withdrawn' else dec(r['amount']) - dec(r['paid_before_period']) - observed_paid)
        packet_ok = True
        by_type = {x['type']: x for x in r['packet']}
        for p in r['packet']:
            packet_supported = cited(p, doc, findings, path + '.packet.' + p['type'])
            packet_ok = packet_ok and packet_supported and p['status'] == 'present' and nonempty(p.get('reference'))
        if not set(doc['policy']['required_packet_types']) <= set(by_type):
            packet_ok = False
        conflict_reviewed = reviewed(r['conflict_review'], path + '.conflict_review')
        conflicts_clear = conflict_reviewed and r['conflict_state'] == 'none-identified' and r['conflict_review']['reviewed_on'] >= r['requested_on']
        has_authority = bool(r['authority_ids']) and all(authority_ok[a] for a in r['authority_ids']) and any('distribution-review' in maps['authority_reviews'][a]['powers'] for a in r['authority_ids'])
        complete = supported and beneficiary_ok[r['beneficiary_id']] and clauses_ok(r['clause_ids'], 'distribution') and has_authority and packet_ok and conflicts_clear and upstream_clear and remaining is not None and r['needed_by'] is not None and r['requested_principal'] is not None and r['requested_income'] is not None
        if not complete:
            add(findings, 'distribution-review-gap', 'Distribution packet needs complete authority, beneficiary/clause, required documents, conflict and payment-history evidence; no entitlement or payment decision made', path)
        if r['conflict_state'] != 'none-identified':
            add(findings, 'distribution-conflict', 'Retain the supplied open or unknown conflict for independent professional review', path, conflict_state=r['conflict_state'])
        if remaining is None:
            add(findings, 'distribution-amount-unknown', 'Outstanding request amount cannot be established from supported request and prior/current settled payments', path)
        if pending and (r['lifecycle'] in {'settled', 'withdrawn'} or (remaining is not None and observed_pending > remaining)):
            complete = False
            add(findings, 'distribution-pending-state-conflict', 'Pending payment records conflict with request state or exceed its remaining amount; resolve without executing', path)
        if r['lifecycle'] not in {'settled', 'withdrawn'} and r['needed_by'] is not None and r['needed_by'] < doc['as_of'] and (remaining is None or remaining > 0):
            add(findings, 'distribution-request-past-needed-date', 'Open request has passed its supplied needed-by date; this is not a legal deadline determination', path)
        if r['lifecycle'] not in {'settled', 'withdrawn'}:
            open_by_account[r['account_id']].append(remaining)
        requests.append(dict(record=deepcopy(r), beneficiary_household_id=maps['beneficiaries'][r['beneficiary_id']]['household_id'], evidence_status='documented-for-human-review' if complete else 'incomplete',
                             observed_current_period_paid=money(observed_paid), observed_pending_payments=money(observed_pending), outstanding_requested_amount=None if remaining is None else money(remaining), entitlement='not-determined', payment_approval='not-given'))
    result['distribution_requests'] = requests
    scenarios = []
    for a in doc['cash_accounts']:
        aid = a['account_id']; amounts = open_by_account[aid]
        known = context_ok and support['cash_accounts'][aid] and covered['distribution_requests'] and reconciled_total[aid] and cash_closing[aid] is not None and a['protected_reserve'] is not None and all(v is not None for v in amounts)
        requested = sum((v for v in amounts if v is not None), ZERO)
        residual = cash_closing[aid] - dec(a['protected_reserve']) - requested if known else None
        if residual is None:
            add(findings, 'distribution-cash-scenario-unknown', 'Reconciled cash, protected reserve and complete supported open requests are required', 'cash_accounts.' + aid)
        elif residual < 0:
            add(findings, 'distribution-cash-scenario-shortfall', 'Illustrative cash after all open requests and reserve is negative; this does not adjudicate any request', 'cash_accounts.' + aid, amount=money(residual))
        scenarios.append(dict(account_id=aid, observed_known_open_requests=money(requested), all_open_requests=None if not known else money(requested),
                              illustrative_cash_after_all_open_requests=None if residual is None else money(residual), funding_authorized=False))
    result['distribution_cash_scenarios'] = scenarios
    result['next_actions'] = [dict(code=f['code'], question=f['message'], evidence_path=f.get('path'), owner='trust administrator / legal reviewer / fiduciary accountant', context={k: deepcopy(v) for k, v in f.items() if k not in {'code', 'message', 'path'}}) for f in findings]
    result['boundaries'] = dict(entitlement_determined=False, authority_authenticated=False, legal_classification_inferred=False, payment_approved=False, system_write=False)
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return validate_result(out, SKILL, build)
