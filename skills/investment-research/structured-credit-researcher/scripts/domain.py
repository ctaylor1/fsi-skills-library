"""Bounded supplied-profile securitization research; no live action or legal interpretation (MIT)."""
from __future__ import annotations
import math
from fractions import Fraction
from analysis_contract import validate_base, number, require, references, finish, rows, unique
from research_runtime import calendar_date, temporal, eligible_time, text, only

SKILL = 'structured-credit-researcher'
PROFILE = 'single-period-sequential-pay-v1'
TEST_BASIS = 'ending-performing-collateral-before-distributions/post-loss-notes'


def exact(value, fields, label):
    require(isinstance(value, dict), label + ' must be an object')
    require(set(value) == set(fields.split()), label + ' requires exactly its documented fields')
    return value


def cite(doc, row, label):
    require(bool(row.get('evidence_refs')), label + ' requires precise citations')
    references(doc, row['evidence_refs'], label + '.evidence_refs')
    require(eligible_time(row.get('known_at'), doc['knowledge_cutoff']) is True,
            label + ' knowledge must be no later than cutoff with compatible precision')
    kind, value = temporal(row['known_at'])
    day = value if kind == 'date' else value.date()
    require(day <= calendar_date(doc['as_of']), label + ' knowledge postdates as_of')
    sources = {s['source_id']: s for s in doc['sources']}
    for ref in row['evidence_refs']:
        require(eligible_time(sources[ref['source_id']]['known_at'], row['known_at']) is True,
                label + ' source knowledge postdates row knowledge or has incompatible precision')
    return day


def fraction(value, label):
    number(value, label, minimum=0)
    require(value <= 1, label + ' must be a fraction from zero to one')


def positive(value, label):
    require(number(value, label, minimum=0) > 0, label + ' must exceed zero')


def validate_document(doc):
    validate_base(doc, subject_types=('security',))
    require(doc.get('schema_version') == 'ir-phase4-structured/1.0', 'schema_version ir-phase4-structured/1.0 required')
    b = exact(doc.get('financial_basis'), 'currency units principal_basis pool_scope', 'financial_basis')
    require(text(b['currency']) and len(b['currency']) == 3 and b['currency'].isalpha() and b['currency'].isupper(), 'uppercase three-letter currency required')
    require(b['units'] in {'ones', 'thousands', 'millions', 'billions'}, 'explicit numeric units required')
    require(b['principal_basis'] == 'outstanding-par' and text(b['pool_scope']), 'outstanding-par and explicit restricted pool_scope required')
    pool = exact(doc.get('pool'), 'pool_id issuer_id trustee_id snapshot_date known_at inventory_complete evidence_refs assets', 'pool')
    for k in ('pool_id', 'issuer_id', 'trustee_id'): require(text(pool[k]), 'pool.' + k + ' required')
    require(pool['issuer_id'] == doc['subject']['issuer_id'], 'pool issuer differs from security issuer')
    require(pool['inventory_complete'] is True, 'complete supplied collateral inventory required; incomplete inventory cannot determine loss support')
    require(calendar_date(pool['snapshot_date']) == calendar_date(doc['as_of']), 'pool snapshot must equal analysis as_of for this one-period opening state')
    require(cite(doc, pool, 'pool') >= calendar_date(pool['snapshot_date']), 'trustee inventory cannot be known before snapshot')
    assets = unique(rows(pool['assets'], 'pool.assets', nonempty=True), 'asset_id', 'assets')
    for a in assets:
        exact(a, 'asset_id obligor_id sector jurisdiction vintage balance eligible eligibility_reason known_at evidence_refs', 'asset')
        for k in ('obligor_id', 'sector', 'jurisdiction', 'vintage', 'eligibility_reason'):
            require(text(a[k]), 'asset.' + k + ' required')
        positive(a['balance'], 'asset.balance')
        require(type(a['eligible']) is bool, 'asset.eligible must be an explicit supplied boolean')
        cite(doc, a, 'asset')
    tr = exact(doc.get('tranches'), 'inventory_complete known_at evidence_refs notes', 'tranches')
    require(tr['inventory_complete'] is True, 'complete supplied tranche inventory required')
    cite(doc, tr, 'tranches')
    notes = unique(rows(tr['notes'], 'tranches.notes', nonempty=True), 'security_id', 'notes')
    ranks = set()
    for n in notes:
        exact(n, 'security_id seniority opening_principal annual_coupon opening_interest_arrears', 'note')
        require(type(n['seniority']) is int and n['seniority'] > 0, 'positive integer seniority required')
        require(n['seniority'] not in ranks, 'equal-rank/pro-rata classes require a separate reviewed engine')
        ranks.add(n['seniority']); positive(n['opening_principal'], 'note.opening_principal')
        fraction(n['annual_coupon'], 'note.annual_coupon')
        require(number(n['opening_interest_arrears'], 'note.opening_interest_arrears', minimum=0) == 0,
                'opening interest arrears unsupported; supply an explicit zero only if established')
    require(doc['subject']['id'] in {n['security_id'] for n in notes}, 'requested security absent from tranche inventory')
    total = math.fsum(a['balance'] for a in assets)
    debt = math.fsum(n['opening_principal'] for n in notes)
    number(total, 'aggregate collateral balance'); number(debt, 'aggregate note principal')
    require(debt <= total, 'opening undercollateralized structures require a separate reviewed engine; no fabricated equity cushion')
    terms = exact(doc.get('reviewed_terms'), 'profile document_id version review_status known_at evidence_refs interest_base loss_priority principal_priority reserve_use opening_reserve trigger', 'reviewed_terms')
    require(terms['profile'] == PROFILE and terms['review_status'] == 'supplied-reviewed-profile', 'explicit supplied-reviewed simplified profile required')
    for k in ('document_id', 'version'): require(text(terms[k]), 'reviewed_terms.' + k + ' required')
    cite(doc, terms, 'reviewed_terms')
    require(terms['interest_base'] == 'opening-note-principal', 'only opening-note coupon accrual supported')
    require(terms['loss_priority'] == 'equity-then-junior-to-senior', 'unsupported loss priority')
    require(terms['principal_priority'] == 'senior-to-junior', 'unsupported principal priority')
    require(terms['reserve_use'] == 'fees-then-interest-only', 'reserve may support fees then interest only')
    number(terms['opening_reserve'], 'opening_reserve', minimum=0)
    trigger = exact(terms['trigger'], 'enabled test_basis minimum_ratio breach_operator action', 'trigger')
    require(type(trigger['enabled']) is bool, 'trigger.enabled requires explicit boolean')
    require(trigger['test_basis'] == TEST_BASIS, 'unsupported trigger observation/order basis')
    require(trigger['breach_operator'] == 'strictly-less-than', 'only explicit strict breach comparison supported')
    require(trigger['action'] == 'divert-excess-interest-to-sequential-principal', 'unsupported trigger action')
    if trigger['enabled']: positive(trigger['minimum_ratio'], 'trigger.minimum_ratio')
    else: require(trigger['minimum_ratio'] is None, 'disabled trigger requires null minimum_ratio')
    sc = exact(doc.get('scenario'), 'scenario_id label kind known_at evidence_refs period_start period_end accrual_year_fraction interest_collections fees_due recovery_timing assumptions', 'scenario')
    require(text(sc['scenario_id']) and text(sc['label']) and sc['kind'] == 'analyst-scenario', 'explicit named analyst scenario required; forecasts cannot be labeled actuals')
    cite(doc, sc, 'scenario')
    require(sc['period_start'] == pool['snapshot_date'], 'scenario must begin at supplied opening snapshot')
    days = (calendar_date(sc['period_end']) - calendar_date(sc['period_start'])).days
    require(0 < days <= 366, 'bounded single-period horizon must be positive and no longer than 366 days; no multi-year accrual compression')
    fraction(sc['accrual_year_fraction'], 'scenario.accrual_year_fraction')
    positive(sc['accrual_year_fraction'], 'scenario.accrual_year_fraction')
    for k in ('interest_collections', 'fees_due'): number(sc[k], 'scenario.' + k, minimum=0)
    require(sc['recovery_timing'] == 'same-period-cash-no-reinstatement', 'only immediate same-period cash recoveries supported; lagged recoveries/reinstatement need separate engine')
    assumptions = unique(rows(sc['assumptions'], 'scenario.assumptions', nonempty=True), 'asset_id', 'assumptions')
    require({a['asset_id'] for a in assets} == {a['asset_id'] for a in assumptions}, 'scenario must cover exactly the supplied asset inventory')
    by_id = {a['asset_id']: a for a in assets}
    for a in assumptions:
        exact(a, 'asset_id default_fraction recovery_fraction scheduled_principal prepay_fraction known_at evidence_refs', 'assumption')
        cite(doc, a, 'assumption')
        for k in ('default_fraction', 'recovery_fraction', 'prepay_fraction'): fraction(a[k], k)
        number(a['scheduled_principal'], 'scheduled_principal', minimum=0)
        require(a['scheduled_principal'] <= by_id[a['asset_id']]['balance'] * (1 - a['default_fraction']),
                'scheduled principal exceeds performing balance after defaults')
    review = exact(doc.get('research_review'), 'requested_topics assessments', 'research_review')
    topics = rows(review['requested_topics'], 'requested_topics', nonempty=True)
    require(all(text(t) for t in topics) and len(set(topics)) == len(topics), 'requested topics must be unique nonempty strings')
    assessments = unique(rows(review['assessments'], 'assessments'), 'topic_id', 'assessments')
    for item in assessments:
        exact(item, 'topic_id status assessment known_at evidence_refs', 'assessment')
        require(item['topic_id'] in topics, 'assessment topic is outside declared requested scope')
        require(item['status'] in {'supplied-reviewed', 'gap'}, 'assessment needs supplied-reviewed or gap status')
        require(text(item['assessment']), 'assessment requires explanatory text, including a gap reason')
        cite(doc, item, 'assessment')
    return []


def exact_trigger_basis(doc):
    """Rebuild comparison values from declared decimal inputs, before binary arithmetic.

    str preserves the accepted JSON numeric value's shortest decimal form. No
    rounded computed ratio, epsilon or materiality tolerance decides a trigger.
    """
    f = lambda value: Fraction(str(value))
    assumptions = {a['asset_id']: a for a in doc['scenario']['assumptions']}
    total, loss, ending = Fraction(0), Fraction(0), Fraction(0)
    for asset in doc['pool']['assets']:
        a = assumptions[asset['asset_id']]
        opening = f(asset['balance']); default = opening * f(a['default_fraction'])
        performing = opening - default - f(a['scheduled_principal'])
        total += opening
        loss += default * (1 - f(a['recovery_fraction']))
        ending += performing * (1 - f(a['prepay_fraction']))
    debt = sum((f(n['opening_principal']) for n in doc['tranches']['notes']), Fraction(0))
    cushion = total - debt
    post_loss_notes = max(Fraction(0), debt - max(Fraction(0), loss - cushion))
    return ending, post_loss_notes


def compute(doc):
    validate_document(doc)
    pool, sc, terms = doc['pool'], doc['scenario'], doc['reviewed_terms']
    assumptions = {a['asset_id']: a for a in sc['assumptions']}
    asset_results = []
    strata = {k: {} for k in ('obligor_id', 'sector', 'jurisdiction', 'vintage')}
    for asset in pool['assets']:
        a = assumptions[asset['asset_id']]; opening = asset['balance']
        default = opening * a['default_fraction']; recovery = default * a['recovery_fraction']
        scheduled = a['scheduled_principal']; prepay = (opening - default - scheduled) * a['prepay_fraction']
        ending = opening - default - scheduled - prepay
        asset_results.append({'asset_id': asset['asset_id'], 'opening_principal': opening, 'defaulted_principal': default,
            'same_period_cash_recovery': recovery, 'realized_scenario_loss': default - recovery,
            'scheduled_principal': scheduled, 'prepaid_principal': prepay, 'ending_performing_principal': ending,
            'principal_collections': scheduled + prepay + recovery, 'eligible_supplied': asset['eligible']})
        for key in strata: strata[key][asset[key]] = strata[key].get(asset[key], 0) + opening
    total = math.fsum(r['opening_principal'] for r in asset_results)
    loss = math.fsum(r['realized_scenario_loss'] for r in asset_results)
    principal_cash = math.fsum(r['principal_collections'] for r in asset_results)
    ending_collateral = math.fsum(r['ending_performing_principal'] for r in asset_results)
    notes = sorted(doc['tranches']['notes'], key=lambda n: n['seniority'])
    debt = math.fsum(n['opening_principal'] for n in notes)
    cushion = total - debt; cushion_used = min(cushion, loss); remaining_loss = loss - cushion_used
    balances = {n['security_id']: n['opening_principal'] for n in notes}; write_downs = {}
    for n in reversed(notes):
        key = n['security_id']; take = min(remaining_loss, balances[key]); write_downs[key] = take
        balances[key] -= take; remaining_loss -= take
    post_loss_debt = math.fsum(balances.values())
    trigger = terms['trigger']
    exact_numerator, exact_denominator = exact_trigger_basis(doc)
    ratio = float(exact_numerator / exact_denominator) if exact_denominator else None
    breached = bool(trigger['enabled'] and exact_denominator > 0
                    and exact_numerator < Fraction(str(trigger['minimum_ratio'])) * exact_denominator)
    interest_cash, reserve = sc['interest_collections'], terms['opening_reserve']
    reserve_draw = 0
    def pay(due):
        nonlocal interest_cash, reserve, reserve_draw
        from_interest = min(interest_cash, due); interest_cash -= from_interest
        from_reserve = min(reserve, due - from_interest); reserve -= from_reserve; reserve_draw += from_reserve
        return from_interest + from_reserve
    fees_paid = pay(sc['fees_due']); fees_unpaid = sc['fees_due'] - fees_paid
    interest = {}
    for n in notes:
        key = n['security_id']; due = n['opening_principal'] * n['annual_coupon'] * sc['accrual_year_fraction']; paid = pay(due)
        interest[key] = {'interest_due': due, 'interest_paid': paid, 'unpaid_interest': due - paid}
    diverted = interest_cash if breached else 0
    residual_interest = interest_cash - diverted
    available_principal = principal_cash + diverted
    principal_paid = {}
    for n in notes:
        key = n['security_id']; paid = min(available_principal, balances[key]); balances[key] -= paid
        available_principal -= paid; principal_paid[key] = paid
    note_results = []
    for n in notes:
        key = n['security_id']; junior_support = math.fsum(m['opening_principal'] for m in notes if m['seniority'] > n['seniority'])
        note_results.append(dict(n, **interest[key], principal_write_down=write_downs[key], principal_paid=principal_paid[key],
            ending_principal=balances[key], opening_subordinate_note_support=junior_support,
            opening_equity_cushion_support=cushion, opening_collateral_loss_attachment_fraction=(junior_support + cushion) / total))
    paid_principal = math.fsum(principal_paid.values()); paid_interest = math.fsum(v['interest_paid'] for v in interest.values())
    cash_sources = principal_cash + sc['interest_collections'] + terms['opening_reserve']
    cash_uses = fees_paid + paid_interest + paid_principal + residual_interest + available_principal + reserve
    collateral_difference = total - ending_collateral - principal_cash - loss
    cash_difference = cash_sources - cash_uses
    loss_difference = loss - cushion_used - math.fsum(write_downs.values())
    for value, label in ((cash_difference, 'cash'), (collateral_difference, 'collateral'), (loss_difference, 'loss')):
        require(abs(value) <= 1e-9 * max(1, total, cash_sources), label + ' conservation failed')
    issues = []
    assessments = {r['topic_id']: r for r in doc['research_review']['assessments']}
    coverage = []
    for topic in doc['research_review']['requested_topics']:
        item = assessments.get(topic)
        state = item['status'] if item else 'not-supplied'
        coverage.append({'topic_id': topic, 'status': state, 'assessment': item['assessment'] if item else None,
                         'evidence_refs': item['evidence_refs'] if item else []})
        if state != 'supplied-reviewed': issues.append('Requested structured-credit research topic ' + topic + ' remains ' + state)
    for a in pool['assets']:
        if not a['eligible']: issues.append('Asset ' + a['asset_id'] + ' is supplied-ineligible; retained in collateral and scenario totals, not silently excluded')
    if fees_unpaid: issues.append('Scenario fees unpaid: ' + str(fees_unpaid))
    for n in note_results:
        if n['unpaid_interest']: issues.append('Scenario interest shortfall for ' + n['security_id'] + ': ' + str(n['unpaid_interest']))
        if n['principal_write_down']: issues.append('Scenario principal write-down for ' + n['security_id'] + ': ' + str(n['principal_write_down']))
    if breached: issues.append('Supplied simplified trigger is breached; excess-interest diversion applied in the declared order')
    concentrations = {key: [{'category': label, 'opening_principal': amount, 'opening_pool_fraction': amount / total}
                           for label, amount in sorted(values.items())] for key, values in strata.items()}
    result = {
        'research_review': {'requested_coverage': coverage, 'assessment_assurance': 'supplied-narrative-not-independently-adjudicated'},
        'profile': PROFILE, 'pool_id': pool['pool_id'], 'trustee_id': pool['trustee_id'], 'financial_basis': doc['financial_basis'],
        'scenario': {k: sc[k] for k in ('scenario_id', 'label', 'kind', 'period_start', 'period_end', 'accrual_year_fraction', 'recovery_timing')},
        'collateral_review': {'opening_principal': total, 'ending_performing_principal': ending_collateral,
            'supplied_eligible_principal': math.fsum(a['balance'] for a in pool['assets'] if a['eligible']),
            'eligibility_independently_verified': False, 'assets': asset_results, 'concentrations': concentrations,
            'largest_obligor_fraction': max(r['opening_pool_fraction'] for r in concentrations['obligor_id'])},
        'loss_allocation': {'scenario_collateral_loss': loss, 'opening_collateral_equity_cushion': cushion,
            'equity_cushion_absorbed': cushion_used, 'remaining_collateral_equity_cushion': cushion - cushion_used,
            'note_principal_write_downs': math.fsum(write_downs.values()), 'unallocated_loss': remaining_loss},
        'trigger_result': {'enabled': trigger['enabled'], 'test_basis': trigger['test_basis'], 'numerator': float(exact_numerator),
            'denominator_post_loss_notes': float(exact_denominator), 'observed_ratio': ratio, 'minimum_ratio': trigger['minimum_ratio'],
            'denominator_zero': exact_denominator == 0,
            'comparison_basis': 'exact-rational-reconstruction-from-declared-decimal-input-values; strict cross-product, no epsilon',
            'comparison_numerator_rational': str(exact_numerator), 'comparison_denominator_rational': str(exact_denominator),
            'observed_ratio_presentation': 'approximate-float-display-only; not the trigger decision', 'breached': breached, 'excess_interest_diverted': diverted,
            'observation_order': 'after collateral defaults, recoveries and prepayments; after note loss allocation; before cash distributions'},
        'waterfall': {'principal_collections': principal_cash, 'interest_collections': sc['interest_collections'],
            'fees_due': sc['fees_due'], 'fees_paid': fees_paid, 'fees_unpaid': fees_unpaid, 'interest_paid': paid_interest,
            'opening_reserve': terms['opening_reserve'], 'reserve_draw_for_fees_and_interest': reserve_draw,
            'ending_reserve': reserve, 'excess_interest_diverted': diverted, 'note_principal_paid': paid_principal,
            'residual_interest_cash': residual_interest, 'residual_principal_cash': available_principal},
        'tranche_results': note_results,
        'conservation': {'cash_sources': cash_sources, 'cash_uses': cash_uses, 'cash_difference': cash_difference,
            'collateral_principal_difference': collateral_difference, 'loss_allocation_difference': loss_difference,
            'closing_performing_collateral_plus_reserve_less_notes': ending_collateral + reserve - math.fsum(balances.values())},
        'review_limitations': [
            'One supplied opening snapshot and one future period; no observed-actual cash-flow assertion or calibrated default probability.',
            'The exact simplified terms are supplied-reviewed, not independently interpreted or legally authenticated; no universal CLO/RMBS/CMBS waterfall support.',
            'Default fractions apply first to opening par; scheduled principal then prepayments reduce surviving par; same-period recoveries are cash only, never reinstated collateral.',
            'Interest collections, fixed fees and year fraction are supplied scenario inputs; no floating-rate reset, day-count derivation, reinvestment, lagged recovery, PIK or prior arrears.',
            'Reserve supports fees then interest and is excluded from principal loss absorption and trigger collateral; excess principal is residual cash.',
            'Eligibility is a supplied assertion; ineligible assets remain in totals and require adjudication. No price, agency rating, regulatory capital, legal opinion or execution determination.'],
        'legal_terms_verified': False, 'agency_rating_assigned': False, 'tranche_price_estimated': False,
    }
    return finish(doc, SKILL, result, issues=issues, lineage=[
        {'formula': 'default = opening par * period default fraction; recovery = default * same-period recovery fraction; loss = default - recovery'},
        {'formula': 'prepay = (opening par - defaults - scheduled principal) * prepay fraction; principal cash = scheduled + prepay + recovery'},
        {'formula': 'loss absorbs opening collateral less notes first, then notes in descending seniority number; principal cash pays ascending seniority number'},
        {'formula': 'coupon due = opening note principal * fixed annual coupon * supplied year fraction; interest and reserve pay fees then note interest'},
        {'formula': 'trigger observed before cash distributions; reconstruct numerator and post-loss denominator with Fraction(str(original numeric value)); compare exact numerator < declared threshold * exact denominator; displayed ratio does not decide breach'},
        {'formula': 'breached trigger diverts remaining interest to sequential note principal, counted once in cash conservation'}])
