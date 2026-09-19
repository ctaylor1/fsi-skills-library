"""Client private-capital ledger and conservative funding review. No external actions."""
from copy import deepcopy
from decimal import Decimal

from wealth_contract import iso_date, make_output, nonempty, source_errors
from wealth_workflow import (add, base_errors, base_findings, cited, common_result,
                             dec, enum, money, number, rows, texts, validate_result)

SKILL = 'private-market-client-reviewer'
ZERO = Decimal(0)
COVERAGE = ('positions_complete', 'notices_complete', 'movements_complete',
            'forecasts_complete', 'other_obligations_complete')


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    as_of = doc['as_of']
    allowed = {'schema_version', 'request_id', 'household_id', 'as_of', 'engagement', 'sources',
               'currency', 'policy', 'upstream_issues', 'coverage', 'accounts', 'positions',
               'notices', 'movements', 'forecasts', 'other_obligations'}
    if set(doc) - allowed:
        errors.append('unsupported top-level fields: ' + ', '.join(sorted(set(doc) - allowed)))

    def required(row, keys, path):
        for key in keys:
            if not nonempty(row.get(key)):
                errors.append(f'{path}.{key} must be nonempty text')

    def amount(row, key, path, nullable=False, positive=False):
        if key not in row or (row[key] is None and not nullable):
            errors.append(f'{path}.{key} is required')
        elif row[key] is not None and (not number(row[key], low='0.01' if positive else 0) or dec(row[key]).as_tuple().exponent < -2):
            errors.append(f'{path}.{key} must be a bounded nonnegative decimal amount')

    def date(row, key, path, nullable=False, future=False):
        value = row.get(key)
        if key not in row or (value is None and not nullable):
            errors.append(f'{path}.{key} is required')
        elif value is not None and (iso_date(value) is None or (not future and value > as_of)):
            errors.append(f'{path}.{key} requires a valid nonfuture date' if not future else f'{path}.{key} requires an ISO date')

    if doc.get('currency') != 'USD':
        errors.append('currency must be USD; FX conversion is not supported')
    for key in ('execute', 'approval', 'subscription', 'redemption', 'transfer'):
        if key in doc:
            errors.append(f'{key} is outside draft review scope')
    policy = doc['policy']
    if type(policy.get('max_nav_age_days')) is not int or not 1 <= policy['max_nav_age_days'] <= 3660:
        errors.append('policy.max_nav_age_days must be an integer 1..3660')
    date(policy, 'horizon_date', 'policy', future=True)
    if iso_date(policy.get('horizon_date')) and policy['horizon_date'] < as_of:
        errors.append('policy.horizon_date cannot precede as_of')
    coverage = doc.get('coverage')
    if not isinstance(coverage, dict):
        errors.append('coverage must be an object')
    else:
        for key in COVERAGE:
            if key not in coverage or (coverage[key] is not None and type(coverage[key]) is not bool):
                errors.append(f'coverage.{key} must be explicit boolean or null')
    accounts = rows(doc, 'accounts', errors, 'account_id')
    positions = rows(doc, 'positions', errors, 'position_id')
    notices = rows(doc, 'notices', errors, 'notice_id')
    movements = rows(doc, 'movements', errors, 'movement_id')
    forecasts = rows(doc, 'forecasts', errors, 'forecast_id')
    obligations = rows(doc, 'other_obligations', errors, 'obligation_id')
    if errors:
        return errors
    account_map = {x['account_id']: x for x in accounts}
    position_map = {x['position_id']: x for x in positions}
    notice_map = {x['notice_id']: x for x in notices}
    account_fund_pairs = set()
    for a in accounts:
        path = 'accounts.' + a['account_id']
        required(a, ('label',), path)
        amount(a, 'available_cash', path, nullable=True)
        amount(a, 'protected_reserve', path, nullable=True)
        if a.get('cash_as_of') != as_of or a.get('cash_basis') != 'available-settled-cash-as-of':
            errors.append(f'{path} requires current settled available cash basis/date')
    for p in positions:
        path = 'positions.' + p['position_id']
        required(p, ('account_id', 'fund_id', 'fund_name'), path)
        if not isinstance(p.get('account_id'), str) or p['account_id'] not in account_map:
            errors.append(f'{path} unknown account_id')
        if nonempty(p.get('fund_id')) and nonempty(p.get('account_id')):
            pair = (p['account_id'], p['fund_id'])
            if pair in account_fund_pairs:
                errors.append('aggregate duplicate account/fund positions before review')
            account_fund_pairs.add(pair)
        amount(p, 'commitment_amount', path, nullable=True)
        if p.get('commitment_basis') != 'current-operative-total-including-amendments':
            errors.append(f'{path} requires current operative total commitment basis')
        date(p, 'inception_date', path)
        for key in ('reported_uncalled', 'reported_outstanding_calls'):
            amount(p, key, path, nullable=True)
        nav = p.get('nav')
        if not isinstance(nav, dict):
            errors.append(f'{path}.nav must be an object')
        else:
            amount(nav, 'amount', path + '.nav', nullable=True)
            date(nav, 'valuation_date', path + '.nav', nullable=True)
            if nav.get('valuation_date') and iso_date(nav['valuation_date']) and iso_date(p.get('inception_date')) and nav['valuation_date'] < p['inception_date']:
                errors.append(f'{path}.nav predates inception')
        requirements = rows(p, 'eligibility_requirements', errors, 'criterion_id')
        evidence = rows(p, 'eligibility_evidence', errors, 'criterion_id')
        requirement_ids = {x.get('criterion_id') for x in requirements if nonempty(x.get('criterion_id'))}
        for r in requirements:
            required(r, ('description', 'legal_basis'), path + '.eligibility_requirements')
            if not texts(r.get('required_documents')):
                errors.append('eligibility requirement needs explicit required_documents identifiers')
        for e in evidence:
            if not isinstance(e.get('criterion_id'), str) or e['criterion_id'] not in requirement_ids:
                errors.append('eligibility evidence criterion_id must match supplied requirement')
            if not enum(e.get('status'), {'documented', 'incomplete', 'unknown', 'not-applicable'}):
                errors.append('eligibility evidence status is invalid')
            required(e, ('rationale',), path + '.eligibility_evidence')
            if e.get('reviewer') is not None and not nonempty(e.get('reviewer')):
                errors.append('eligibility reviewer must be nonempty or null')
            date(e, 'review_date', path, nullable=True)
            date(e, 'review_by', path, nullable=True, future=True)
            if iso_date(e.get('review_date')) and iso_date(e.get('review_by')) and e['review_by'] < e['review_date']:
                errors.append('eligibility review_by precedes review_date')
            if not texts(e.get('document_refs'), allow_empty=True):
                errors.append('eligibility document_refs must be a unique text list')
        diligence = p.get('manager_diligence')
        if 'manager_diligence' not in p:
            errors.append(f'{path}.manager_diligence must be object or explicit null')
        elif diligence is not None:
            if not isinstance(diligence, dict):
                errors.append(f'{path}.manager_diligence must be object or null')
            else:
                required(diligence, ('artifact_id', 'input_hash'), path)
                digest = diligence.get('input_hash')
                if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                    errors.append('manager diligence input_hash must be a SHA256 digest')
                if not enum(diligence.get('status'), {'review-ready', 'needs-data'}):
                    errors.append('manager diligence status is invalid')
                date(diligence, 'review_date', path)
                date(diligence, 'review_by', path, future=True)
                if iso_date(diligence.get('review_date')) and iso_date(diligence.get('review_by')) and diligence['review_by'] < diligence['review_date']:
                    errors.append('manager review_by precedes review_date')
    for n in notices:
        path = 'notices.' + n['notice_id']
        if not isinstance(n.get('position_id'), str) or n['position_id'] not in position_map:
            errors.append(f'{path} unknown position_id')
        if not enum(n.get('kind'), {'call', 'distribution'}):
            errors.append(f'{path} kind must be call or distribution')
        if not enum(n.get('lifecycle'), {'notice', 'partially-settled', 'settled', 'cancelled'}):
            errors.append(f'{path} lifecycle is invalid')
        if not enum(n.get('purpose'), {'investment', 'management-fee', 'expense', 'proceeds', 'other'}):
            errors.append(f'{path} purpose is invalid')
        options = {'inside-commitment', 'outside-commitment', 'mixed'} if n.get('kind') == 'call' else {'recallable', 'non-recallable', 'mixed'}
        if not enum(n.get('classification'), options):
            errors.append(f'{path} classification is invalid for kind')
        amount(n, 'amount', path, positive=True)
        amount(n, 'commitment_effect_amount', path, nullable=True)
        date(n, 'notice_date', path)
        date(n, 'due_date', path, future=True)
        if iso_date(n.get('notice_date')) and iso_date(n.get('due_date')) and n['due_date'] < n['notice_date']:
            errors.append(f'{path} due_date precedes notice_date')
        if isinstance(n.get('position_id'), str) and n['position_id'] in position_map and iso_date(n.get('notice_date')) and iso_date(position_map[n['position_id']].get('inception_date')) and n['notice_date'] < position_map[n['position_id']]['inception_date']:
            errors.append(f'{path} predates position inception')
        if number(n.get('amount')) and number(n.get('commitment_effect_amount')):
            a, c = dec(n['amount']), dec(n['commitment_effect_amount'])
            if c > a or (n.get('classification') in {'inside-commitment', 'recallable'} and c != a) or (n.get('classification') in {'outside-commitment', 'non-recallable'} and c != 0) or (n.get('classification') == 'mixed' and not 0 < c < a):
                errors.append(f'{path} classification and commitment effect disagree')
    for m in movements:
        path = 'movements.' + m['movement_id']
        if not isinstance(m.get('notice_id'), str) or m['notice_id'] not in notice_map:
            errors.append(f'{path} unknown notice_id')
        amount(m, 'amount', path, positive=True)
        amount(m, 'commitment_effect_amount', path, nullable=True)
        date(m, 'settled_date', path)
        if not enum(m.get('external_flow_scope'), {'within-household', 'outside-household'}):
            errors.append(f'{path} requires explicit external_flow_scope')
        if number(m.get('amount')) and number(m.get('commitment_effect_amount')) and dec(m['commitment_effect_amount']) > dec(m['amount']):
            errors.append(f'{path} commitment effect exceeds cash amount')
        if isinstance(m.get('notice_id'), str) and m['notice_id'] in notice_map:
            n = notice_map[m['notice_id']]
            if iso_date(m.get('settled_date')) and iso_date(n.get('notice_date')) and m['settled_date'] < n['notice_date']:
                errors.append(f'{path} settlement predates notice')
    for f in forecasts:
        path = 'forecasts.' + f['forecast_id']
        if not isinstance(f.get('position_id'), str) or f['position_id'] not in position_map:
            errors.append(f'{path} unknown position_id')
        if not enum(f.get('lifecycle'), {'active', 'superseded', 'cancelled'}):
            errors.append(f'{path} invalid lifecycle')
        if f.get('scope') != 'incremental-to-notices':
            errors.append(f'{path} scope must be incremental-to-notices')
        amount(f, 'amount', path, nullable=True)
        date(f, 'expected_date', path, future=True)
        if iso_date(f.get('expected_date')) and f['expected_date'] < as_of:
            errors.append(f'{path} forecast cannot precede as_of')
        ref = f.get('superseded_by_notice_id')
        if f.get('lifecycle') == 'superseded':
            if not isinstance(ref, str) or ref not in notice_map or notice_map[ref].get('kind') != 'call' or notice_map[ref].get('position_id') != f.get('position_id'):
                errors.append(f'{path} requires matching replacement call notice')
        elif ref is not None or 'superseded_by_notice_id' not in f:
            errors.append(f'{path} superseded_by_notice_id must be explicit null')
    for o in obligations:
        path = 'other_obligations.' + o['obligation_id']
        if not isinstance(o.get('account_id'), str) or o['account_id'] not in account_map:
            errors.append(f'{path} unknown account_id')
        required(o, ('description',), path)
        amount(o, 'amount', path, nullable=True)
        date(o, 'due_date', path, future=True)
        if not enum(o.get('lifecycle'), {'unpaid', 'settled', 'cancelled'}):
            errors.append(f'{path} lifecycle is invalid')
        if o.get('scope') != 'excludes-private-capital-notices':
            errors.append(f'{path} must exclude private notices to prevent duplicate obligations')
    if errors:
        return errors
    for n in notices:
        linked = [m for m in movements if m['notice_id'] == n['notice_id']]
        paid = sum((dec(m['amount']) for m in linked), ZERO)
        amount_n = dec(n['amount'])
        life = n['lifecycle']
        if paid > amount_n or (life in {'notice', 'cancelled'} and paid != 0) or (life == 'settled' and paid != amount_n) or (life == 'partially-settled' and not 0 < paid < amount_n):
            errors.append(f"notices.{n['notice_id']} lifecycle/cash settlements do not reconcile")
        if n['commitment_effect_amount'] is not None and all(m['commitment_effect_amount'] is not None for m in linked):
            effect = sum((dec(m['commitment_effect_amount']) for m in linked), ZERO)
            remaining_effect = dec(n['commitment_effect_amount']) - effect
            if remaining_effect < 0 or remaining_effect > amount_n - paid or (life == 'settled' and remaining_effect != 0):
                errors.append(f"notices.{n['notice_id']} commitment effects do not reconcile")
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError('; '.join(errors))
    findings = base_findings(doc)
    result = common_result(doc)
    coverage = doc['coverage']
    coverage_supported = cited(coverage, doc, findings, 'coverage')
    context_supported = not source_errors(doc['policy'].get('source_ids'), doc) and not source_errors(doc['engagement'].get('source_ids'), doc)
    for key in COVERAGE:
        if coverage[key] is not True:
            add(findings, 'incomplete-inventory', f'{key} is not affirmatively complete', 'coverage.' + key)
    if not doc['positions'] or not doc['accounts']:
        add(findings, 'empty-scope', 'A client private-market review requires at least one position and funding account', 'positions/accounts')
    support = {}
    identifiers = {'accounts': 'account_id', 'positions': 'position_id', 'notices': 'notice_id',
                   'movements': 'movement_id', 'forecasts': 'forecast_id', 'other_obligations': 'obligation_id'}
    for register in identifiers:
        support[register] = {}
        for index, row in enumerate(doc[register]):
            support[register][row[identifiers[register]]] = cited(row, doc, findings, f'{register}[{index}]')
    notices = []
    for n in doc['notices']:
        movements = [m for m in doc['movements'] if m['notice_id'] == n['notice_id']]
        settled = sum((dec(m['amount']) for m in movements), ZERO)
        effect_known = all(m['commitment_effect_amount'] is not None for m in movements)
        settled_effect = sum((dec(m['commitment_effect_amount']) for m in movements), ZERO) if effect_known else None
        if n['commitment_effect_amount'] is None or not effect_known:
            add(findings, 'unknown-commitment-effect', 'Obtain the contractual inside/outside or recallable allocation; no inferred classification amount', 'notices.' + n['notice_id'])
        outstanding = ZERO if n['lifecycle'] == 'cancelled' else dec(n['amount']) - settled
        effect = None if settled_effect is None or n['commitment_effect_amount'] is None else (ZERO if n['lifecycle'] == 'cancelled' else dec(n['commitment_effect_amount']) - settled_effect)
        if outstanding and n['due_date'] < doc['as_of']:
            add(findings, 'overdue-notice', 'Unsettled notice amount is past its supplied due date', 'notices.' + n['notice_id'])
        notices.append(dict(record=deepcopy(n), settled_amount=money(settled),
                            calculation_basis='observed-supplied-records',
                            evidence_supported=support['notices'][n['notice_id']] and all(support['movements'][m['movement_id']] for m in movements),
                            settled_commitment_effect=None if settled_effect is None else money(settled_effect),
                            outstanding_amount=money(outstanding),
                            outstanding_commitment_effect=None if effect is None else money(effect),
                            movements=deepcopy(movements)))
    position_results = []
    ledger_complete = context_supported and coverage_supported and all(coverage[k] is True for k in ('positions_complete', 'notices_complete', 'movements_complete'))
    for p in doc['positions']:
        pid = p['position_id']
        pn = [n for n in notices if n['record']['position_id'] == pid]
        position_supported = support['positions'][pid] and support['accounts'][p['account_id']]
        cash_evidence_complete = ledger_complete and position_supported and all(n['evidence_supported'] for n in pn)
        complete = cash_evidence_complete and p['commitment_amount'] is not None and all(n['settled_commitment_effect'] is not None and n['outstanding_commitment_effect'] is not None for n in pn)
        calls_paid = sum((dec(n['settled_amount']) for n in pn if n['record']['kind'] == 'call'), ZERO)
        distributed = sum((dec(n['settled_amount']) for n in pn if n['record']['kind'] == 'distribution'), ZERO)
        outstanding = sum((dec(n['outstanding_amount']) for n in pn if n['record']['kind'] == 'call'), ZERO)
        remaining = uncalled = reserved = None
        if complete:
            contributed_effect = sum((dec(n['settled_commitment_effect']) for n in pn if n['record']['kind'] == 'call'), ZERO)
            recalled_effect = sum((dec(n['settled_commitment_effect']) for n in pn if n['record']['kind'] == 'distribution'), ZERO)
            remaining = dec(p['commitment_amount']) - contributed_effect + recalled_effect
            reserved = sum((dec(n['outstanding_commitment_effect']) for n in pn if n['record']['kind'] == 'call'), ZERO)
            uncalled = remaining - reserved
            if uncalled < 0:
                add(findings, 'commitment-overdrawn', 'Known contributions and reserved calls exceed the operative commitment plus settled recallable distributions', 'positions.' + pid)
        else:
            add(findings, 'unknown-commitment-balance', 'Complete since-inception ledger, current commitment and effect allocations are required', 'positions.' + pid)
        for key, computed in (('reported_uncalled', uncalled), ('reported_outstanding_calls', outstanding if cash_evidence_complete else None)):
            if p[key] is None:
                add(findings, 'missing-reconciliation', f'{key} statement balance is unknown', 'positions.' + pid)
            elif computed is not None and abs(dec(p[key]) - computed) > dec('0.01'):
                add(findings, 'statement-mismatch', f'{key} differs from reconstructed amount', 'positions.' + pid, reported=money(p[key]), reconstructed=money(computed))
        nav = p['nav']
        nav_supported = cited(nav, doc, findings, 'positions.' + pid + '.nav')
        age = None if nav['valuation_date'] is None else (iso_date(doc['as_of']) - iso_date(nav['valuation_date'])).days
        nav_current = context_supported and position_supported and nav_supported and nav['amount'] is not None and age is not None and age <= doc['policy']['max_nav_age_days']
        if not nav_current:
            add(findings, 'nav-unknown-or-stale', 'No current supported NAV under the supplied review policy; no mark inferred from cash flows', 'positions.' + pid + '.nav')
        eligibility = []
        if not p['eligibility_requirements']:
            add(findings, 'eligibility-policy-gap', 'Supply fund/account-specific legal eligibility review requirements; no universal investor classification assumed', 'positions.' + pid)
        for req in p['eligibility_requirements']:
            requirement_supported = cited(req, doc, findings, 'positions.' + pid + '.eligibility_requirements.' + req['criterion_id'])
            evid = next((e for e in p['eligibility_evidence'] if e['criterion_id'] == req['criterion_id']), None)
            complete_evidence = evid is not None
            if evid is not None:
                evidence_supported = cited(evid, doc, findings, 'positions.' + pid + '.eligibility_evidence.' + req['criterion_id'])
                complete_evidence = context_supported and position_supported and requirement_supported and evidence_supported
                complete_evidence = complete_evidence and evid['status'] == 'documented' and nonempty(evid.get('reviewer')) and evid['review_date'] is not None and evid['review_by'] is not None and evid['review_by'] >= doc['as_of'] and set(req['required_documents']) <= set(evid['document_refs'])
            if not complete_evidence:
                add(findings, 'eligibility-evidence-gap', 'Required legal eligibility evidence needs an attributed current substantive review; no eligibility decision made', 'positions.' + pid + '.eligibility.' + req['criterion_id'])
            eligibility.append(dict(requirement=deepcopy(req), evidence=deepcopy(evid), evidence_status='documented-for-human-review' if complete_evidence else 'incomplete', eligibility_decision='not-determined'))
        diligence = p['manager_diligence']
        if diligence is None:
            add(findings, 'manager-diligence-gap', 'Obtain shared manager diligence and carry all unresolved findings; this workflow does not reproduce manager research', 'positions.' + pid)
        else:
            cited(diligence, doc, findings, 'positions.' + pid + '.manager_diligence')
            if diligence['status'] != 'review-ready' or diligence['review_by'] < doc['as_of']:
                add(findings, 'manager-diligence-gap', 'Referenced manager diligence has open items or needs refresh', 'positions.' + pid, upstream_artifact_id=diligence['artifact_id'])
        post_nav = [m for n in pn for m in n['movements'] if nav['valuation_date'] is not None and m['settled_date'] > nav['valuation_date']]
        position_results.append(dict(position=deepcopy(p), ledger_complete=complete,
                                     observed_settled_calls=money(calls_paid), observed_settled_distributions=money(distributed),
                                     outstanding_calls=money(outstanding) if cash_evidence_complete else None,
                                     remaining_commitment_including_unpaid_calls=None if remaining is None else money(remaining),
                                     reserved_commitment_in_unpaid_calls=None if reserved is None else money(reserved),
                                     uncalled_commitment=None if uncalled is None else money(uncalled),
                                     uncalled_plus_outstanding_calls=None if uncalled is None else money(uncalled + outstanding),
                                     nav_age_days=age, nav_current_under_policy=nav_current,
                                     post_nav_movements=deepcopy(post_nav), eligibility_review=eligibility))
    result['positions'] = position_results
    result['notice_ledger'] = notices
    result['settled_movements'] = []
    for m in doc['movements']:
        n = next(n for n in doc['notices'] if n['notice_id'] == m['notice_id'])
        p = next(p for p in doc['positions'] if p['position_id'] == n['position_id'])
        result['settled_movements'].append(dict(deepcopy(m), kind=n['kind'], position_id=p['position_id'], account_id=p['account_id'], fund_id=p['fund_id']))
    result['forecasts'] = deepcopy(doc['forecasts'])
    result['other_obligations'] = deepcopy(doc['other_obligations'])
    result['fund_summaries'] = []
    for fund in sorted({p['fund_id'] for p in doc['positions']}):
        members = [p for p in position_results if p['position']['fund_id'] == fund]
        summary = dict(fund_id=fund, position_ids=[p['position']['position_id'] for p in members])
        for key in ('outstanding_calls', 'remaining_commitment_including_unpaid_calls', 'reserved_commitment_in_unpaid_calls', 'uncalled_commitment'):
            summary[key] = money(sum((dec(p[key]) for p in members), ZERO)) if all(p[key] is not None for p in members) else None
        summary['current_policy_nav'] = money(sum((dec(p['position']['nav']['amount']) for p in members), ZERO)) if coverage_supported and coverage['positions_complete'] is True and all(p['nav_current_under_policy'] for p in members) else None
        result['fund_summaries'].append(summary)
    budgets = []
    for a in doc['accounts']:
        aid = a['account_id']
        pids = {p['position_id'] for p in doc['positions'] if p['account_id'] == aid}
        events = []
        for n in notices:
            record = n['record']
            if record['position_id'] in pids and record['kind'] == 'call' and dec(n['outstanding_amount']) > 0:
                events.append(dict(date=max(doc['as_of'], record['due_date']), kind='noticed-call', reference=record['notice_id'], amount=n['outstanding_amount'], evidence_supported=n['evidence_supported'], source_ids=record.get('source_ids')))
        for o in doc['other_obligations']:
            if o['account_id'] == aid and o['lifecycle'] == 'unpaid':
                events.append(dict(date=max(doc['as_of'], o['due_date']), kind='other-obligation', reference=o['obligation_id'], amount=o['amount'], evidence_supported=support['other_obligations'][o['obligation_id']], source_ids=o.get('source_ids')))
        for f in doc['forecasts']:
            if f['position_id'] in pids and f['lifecycle'] == 'active':
                events.append(dict(date=f['expected_date'], kind='forecast-call', reference=f['forecast_id'], amount=f['amount'], evidence_supported=support['forecasts'][f['forecast_id']], source_ids=f.get('source_ids')))
        events.sort(key=lambda e: (e['date'], e['kind'], e['reference']))
        cash_observed = a['available_cash'] is not None and a['protected_reserve'] is not None
        observed_initial = dec(a['available_cash']) - dec(a['protected_reserve']) if cash_observed else None
        cash_known = cash_observed and context_supported and support['accounts'][aid]
        initial = observed_initial if cash_known else None
        if not cash_known:
            add(findings, 'liquidity-data-gap', 'Available cash, protected reserve or supporting account/context evidence is unknown', 'accounts.' + aid)
        account_ledger_supported = all(support['positions'][pid] for pid in pids) and all(n['evidence_supported'] for n in notices if n['record']['position_id'] in pids)
        committed_complete = cash_known and coverage_supported and account_ledger_supported and all(coverage[k] is True for k in ('positions_complete', 'notices_complete', 'movements_complete', 'other_obligations_complete'))
        scenario_complete = committed_complete and coverage['forecasts_complete'] is True
        committed = initial if committed_complete else None
        scenario = initial if scenario_complete else None
        if initial is not None and initial < 0:
            add(findings, 'reserve-shortfall', 'Available cash is below the protected reserve before calls', 'accounts.' + aid)
        schedule = []
        for e in events:
            if e['date'] > doc['policy']['horizon_date']:
                continue
            if not e['evidence_supported']:
                scenario = None
                if e['kind'] != 'forecast-call':
                    committed = None
            if e['amount'] is None:
                add(findings, 'unknown-obligation', 'Dated obligation or active forecast has unknown amount', 'accounts.' + aid, reference=e['reference'])
                scenario = None
                if e['kind'] != 'forecast-call':
                    committed = None
            else:
                if scenario is not None:
                    scenario -= dec(e['amount'])
                if committed is not None and e['kind'] != 'forecast-call':
                    committed -= dec(e['amount'])
            schedule.append(dict(e, amount=None if e['amount'] is None else money(e['amount']), committed_balance=None if committed is None else money(committed), forecast_scenario_balance=None if scenario is None else money(scenario)))
            if committed is not None and committed < 0:
                add(findings, 'call-funding-shortfall', 'This account cannot cover dated known obligations while preserving its reserve', 'accounts.' + aid, date=e['date'], balance=money(committed))
            elif scenario is not None and scenario < 0:
                add(findings, 'forecast-funding-shortfall', 'Incremental forecast scenario exceeds available account cash after known obligations and reserve', 'accounts.' + aid, date=e['date'], balance=money(scenario))
        budgets.append(dict(account=deepcopy(a), opening_cash_after_reserve=None if initial is None else money(initial), schedule=schedule,
                            observed_opening_cash_after_reserve=None if observed_initial is None else money(observed_initial),
                            horizon_committed_balance=None if committed is None else money(committed), horizon_forecast_balance=None if scenario is None else money(scenario),
                            excluded_beyond_horizon=[deepcopy(e) for e in events if e['date'] > doc['policy']['horizon_date']],
                            distribution_credit='none; unsettled distributions are not spendable cash'))
    result['account_liquidity'] = budgets
    result['household_liquidity'] = dict(currency='USD', horizon_date=doc['policy']['horizon_date'], transfer_authority_assumed=False)
    for key in ('horizon_committed_balance', 'horizon_forecast_balance'):
        result['household_liquidity'][key] = money(sum((dec(a[key]) for a in budgets), ZERO)) if budgets and all(a[key] is not None for a in budgets) else None
    result['specialist_questions'] = [dict(code=f['code'], question=f['message'], evidence_path=f.get('path'), owner='wealth advisor / fund administrator / legal eligibility reviewer', context={k: deepcopy(v) for k, v in f.items() if k not in {'code', 'message', 'path'}}) for f in findings]
    result['eligibility_decision'] = 'not-determined'
    result['investment_recommendation'] = 'not-made'
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return validate_result(out, SKILL, build)
